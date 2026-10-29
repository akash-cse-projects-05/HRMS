from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import re
import uuid

router = APIRouter(prefix="/api/recruiter", tags=["AI Recruiter & Interview"])

# Skill Taxonomy for semantic match scoring
ROLE_TAXONOMY = {
    "SOFTWARE ENGINEER": [
        "python", "javascript", "typescript", "node.js", "react", "express",
        "mongodb", "sql", "aws", "docker", "git", "rest api", "graphql", "redis"
    ],
    "FULL STACK DEVELOPER": [
        "javascript", "typescript", "react", "next.js", "node.js", "express",
        "mongodb", "postgresql", "html5", "css3", "git", "aws", "rest api", "docker"
    ],
    "DATA SCIENTIST": [
        "python", "machine learning", "deep learning", "pandas", "numpy", "scikit-learn",
        "tensorflow", "pytorch", "sql", "statistics", "data analysis", "tableau"
    ],
    "ACCOUNTS MANAGER": [
        "tally", "gst", "tds", "financial reporting", "auditing", "taxation",
        "bookkeeping", "invoicing", "excel", "balance sheet", "payroll", "quickbooks"
    ],
    "HR MANAGER": [
        "recruitment", "onboarding", "payroll", "employee relations", "performance management",
        "labor laws", "talent acquisition", "hris", "compliance", "conflict resolution"
    ],
    "OPERATIONS MANAGER": [
        "supply chain", "logistics", "vendor management", "inventory", "route optimization",
        "fleet management", "dispatch", "kpi tracking", "procurement", "warehouse"
    ],
    "SALES LEAD": [
        "lead generation", "crm", "salesforce", "b2b", "negotiation", "client acquisition",
        "pipeline management", "closing", "cold outreach", "revenue growth"
    ]
}

RESUME_INDICATORS = [
    "experience", "education", "skills", "projects", "contact", "email",
    "phone", "summary", "profile", "work", "curriculum vitae", "bachelor",
    "master", "technologies", "certifications", "history", "employment",
    "objective", "languages", "developer", "engineer", "manager", "qualifications"
]

def check_is_valid_resume(text: str) -> tuple[bool, str]:
    cleaned = text.strip()
    if len(cleaned) < 50:
        return False, "File content is too short (less than 50 characters) to be a valid resume."
    text_lower = cleaned.lower()
    matches = sum(1 for kw in RESUME_INDICATORS if kw in text_lower)
    if matches < 2:
        return False, "Document does not appear to be a candidate resume (missing standard resume sections like experience, skills, education, or contact details)."
    return True, "Valid resume document"

def clean_and_tokenize(text: str) -> set:
    text = text.lower()
    tokens = set(re.findall(r"\b[a-z0-9+#\.-]+\b", text))
    return tokens

def extract_email(text: str) -> str:
    m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return m.group(0).lower() if m else ""

def extract_phone(text: str) -> str:
    # Match international or local phone numbers
    m = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', text)
    if m:
        digits = re.sub(r'\D', '', m.group(0))
        if len(digits) >= 10:
            return m.group(0).strip()
    return ""

def extract_years_of_experience(text: str) -> float:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b[^.\n]{0,40}?\b(?:experience|exp)\b",
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience",
        r"experience\s*:\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+in\b",
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+as\s+a\b"
    ]
    max_exp = 0.0
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            try:
                val = float(m)
                if 0.5 <= val <= 40:
                    max_exp = max(max_exp, val)
            except ValueError:
                pass
    return max_exp

# --- Pydantic Request Models ---
class ResumeScreenRequest(BaseModel):
    resume_text: str
    target_role: str
    department: Optional[str] = "GENERAL"
    candidate_name: Optional[str] = "Candidate"

class InterviewQuestionGenRequest(BaseModel):
    target_role: Optional[str] = "GENERAL"
    prompt: Optional[str] = ""
    skills: List[str] = []
    department: Optional[str] = "GENERAL"
    question_count: Optional[int] = 5
    difficulty: Optional[str] = "MID"

class CandidateAnswerItem(BaseModel):
    question_id: str
    category: str
    question_text: str
    expected_keywords: List[str] = []
    candidate_answer: str

class InterviewEvaluateRequest(BaseModel):
    target_role: str
    answers: List[CandidateAnswerItem]

# --- 1. POST /api/recruiter/screen ---
@router.post("/screen")
async def screen_resume(payload: ResumeScreenRequest):
    text = payload.resume_text.strip()
    role_key = payload.target_role.strip().upper()
    
    if not text:
        raise HTTPException(status_code=400, detail="Resume text is empty")

    is_valid, reason = check_is_valid_resume(text)
    if not is_valid:
        raise HTTPException(status_code=422, detail=reason)

    # Normalize role key lookup
    expected_skills = None
    for k in ROLE_TAXONOMY:
        if k in role_key or role_key in k:
            expected_skills = ROLE_TAXONOMY[k]
            break
    if not expected_skills:
        expected_skills = ROLE_TAXONOMY["SOFTWARE ENGINEER"]

    resume_tokens = clean_and_tokenize(text)

    matched_skills = []
    missing_skills = []

    for skill in expected_skills:
        skill_lower = skill.lower()
        if skill_lower in text.lower() or set(skill_lower.split()).issubset(resume_tokens):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    # Calculate match score
    num_matched = len(matched_skills)
    skill_score = min(60.0, (num_matched / min(len(expected_skills), 6)) * 60.0)

    exp_years = extract_years_of_experience(text)
    if exp_years >= 5.0:
        exp_score = 25.0
    elif exp_years >= 3.0:
        exp_score = 20.0
    elif exp_years >= 1.0:
        exp_score = 15.0
    elif exp_years > 0:
        exp_score = 8.0
    else:
        exp_score = 5.0

    edu_score = 10.0 if re.search(r'\b(degree|bachelor|master|b\.?tech|m\.?tech|bca|mca|phd|bs|ms)\b', text, re.IGNORECASE) else 5.0
    
    extracted_email = extract_email(text)
    extracted_phone = extract_phone(text)
    contact_score = 5.0 if (extracted_email and extracted_phone) else 2.5

    base_score = round(min(100.0, skill_score + exp_score + edu_score + contact_score), 1)

    # Fast-track triage for immediate call / recruitment
    call_immediately = False
    if base_score >= 80.0 or (num_matched >= 4 and exp_years >= 2.0):
        recommendation = "STRONG_HIRE"
        call_immediately = True
        action_summary = "Call Candidate Immediately & Fast-Track Hire"
    elif base_score >= 65.0:
        recommendation = "SHORTLIST"
        action_summary = "Shortlist for Screening / AI Exam"
    elif base_score >= 48.0:
        recommendation = "HOLD"
        action_summary = "Under Review / Keep on Hold"
    else:
        recommendation = "REJECT"
        action_summary = "Not Suitable / Reject"

    strengths = [
        f"Demonstrated core competence in {', '.join(matched_skills[:5])}" if matched_skills else "General technical skills present",
        f"Approx. {exp_years:.1f} years of relevant industry experience identified" if exp_years > 0 else "Early career profile",
    ]
    if call_immediately:
        strengths.insert(0, "🔥 Priority Candidate: High competency match - Recommended for immediate phone call / fast-track recruitment")

    concerns = [
        f"Missing expected role skills: {', '.join(missing_skills[:4])}" if missing_skills else "No major skill gaps identified"
    ]

    summary = (
        f"{payload.candidate_name}: {base_score}% match for {payload.target_role}. "
        f"Extracted {len(matched_skills)} core skills ({', '.join(matched_skills[:4]) or 'None'}). "
        f"Recommendation: {recommendation} ({action_summary})."
    )

    return {
        "score": base_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "experience_years": exp_years,
        "recommendation": recommendation,
        "call_immediately": call_immediately,
        "action_summary": action_summary,
        "email": extracted_email,
        "phone": extracted_phone,
        "strengths": strengths,
        "concerns": concerns,
        "summary": summary
    }

# --- 2. POST /api/recruiter/generate-questions ---
@router.post("/generate-questions")
async def generate_interview_questions(payload: InterviewQuestionGenRequest):
    prompt_text = (payload.prompt or "").strip()
    role = (payload.target_role or "General").strip()
    difficulty = (payload.difficulty or "MID").upper()

    # 1. Determine question count (prefer explicit prompt mention like '5 questions' or payload count)
    target_count = payload.question_count or 5
    count_match = re.search(r'(\d+)\s*questions?', prompt_text, re.IGNORECASE)
    if count_match:
        try:
            target_count = int(count_match.group(1))
        except ValueError:
            pass
    target_count = max(1, min(15, target_count))

    # 2. Extract domain keywords and detect topic
    prompt_lower = (prompt_text + " " + role).lower()

    questions = []

    # Domain A: Electronics, Hardware, Embedded & Circuits
    if any(k in prompt_lower for k in ["electronic", "circuit", "embedded", "hardware", "microcontroller", "vlsi", "semiconductor", "pcb", "iot", "sensor", "analog", "digital logic", "bjt", "mosfet", "fpga", "arm"]):
        topic_title = "Electronics & Embedded Hardware"
        electronics_bank = [
            {
                "category": "Electronics & Semiconductors",
                "question_text": "Explain the operational differences between a BJT and a MOSFET when used in switching circuits. How do gate capacitance, threshold voltage (Vth), and RDS(on) influence power loss and switching speed?",
                "expected_keywords": ["bjt", "mosfet", "gate capacitance", "rds(on)", "switching speed", "threshold voltage", "saturation", "power dissipation"],
                "time_limit_seconds": 120,
                "evaluation_criteria": "Understanding of voltage-controlled vs current-controlled switches, gate drive dynamics, and thermal considerations."
            },
            {
                "category": "Circuit & Embedded Design",
                "question_text": "When interfacing an analog sensor with a microcontroller's ADC, how do you determine the required sampling rate according to the Nyquist theorem? What role do anti-aliasing filters and decoupling capacitors play?",
                "expected_keywords": ["nyquist", "sampling rate", "anti-aliasing", "decoupling capacitors", "adc", "aliasing", "low-pass filter", "signal to noise ratio"],
                "time_limit_seconds": 120,
                "evaluation_criteria": "Knowledge of mixed-signal design, Nyquist criteria, low-pass RC filtering, and noise suppression."
            },
            {
                "category": "Protocols & Bus Debugging",
                "question_text": "Compare I2C, SPI, and UART communication protocols in terms of speed, bus topology, and wire count. When debugging an I2C bus hang or missing ACK with an oscilloscope, what specific signal integrity issues do you inspect?",
                "expected_keywords": ["i2c", "spi", "uart", "pull-up resistors", "clock stretching", "bus capacitance", "ack/nack", "oscilloscope", "rise time"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Comparative protocol analysis, open-drain pull-up sizing, signal rise times, and debugging methodology."
            },
            {
                "category": "Power & Thermal Management",
                "question_text": "In embedded board design, contrast a Linear Low-Dropout Regulator (LDO) with a Switched-Mode Power Supply (SMPS) regarding efficiency, output voltage ripple, and PCB thermal dissipation.",
                "expected_keywords": ["ldo", "smps", "efficiency", "ripple", "thermal dissipation", "buck converter", "inductor", "switching frequency", "noise"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Power architecture trade-offs, inductor and capacitor selection, and heat sinking in battery-operated vs line-powered devices."
            },
            {
                "category": "PCB Layout & Signal Integrity",
                "question_text": "Describe best practices for PCB layout to minimize electromagnetic interference (EMI) and ground bounce. How should analog and digital ground planes be organized, and where should bypass capacitors be placed?",
                "expected_keywords": ["ground plane", "ground bounce", "emi", "bypass capacitors", "trace impedance", "return path", "star ground", "decoupling"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "PCB physical design rules, high-frequency return paths, and proper placement of 0.1uF / 10uF bypass capacitors adjacent to IC power pins."
            },
            {
                "category": "Operational Amplifiers & Analog Conditioning",
                "question_text": "How do you select an Operational Amplifier for precision sensor signal conditioning? Explain the importance of Gain-Bandwidth Product (GBWP), Input Offset Voltage, and Common-Mode Rejection Ratio (CMRR).",
                "expected_keywords": ["op-amp", "gain-bandwidth product", "offset voltage", "cmrr", "feedback loop", "signal conditioning", "instrumentation amplifier"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Analog signal chain fundamentals, noise budgeting, and precision amplification."
            },
            {
                "category": "Firmware & Hardware Troubleshooting",
                "question_text": "During firmware development for an ARM microcontroller, you observe intermittent microcontroller resets when a motor or relay triggers. What root causes (brown-out, inductive kickback, flyback diode, watchdog timer) would you test for?",
                "expected_keywords": ["inductive kickback", "flyback diode", "brown-out reset", "watchdog timer", "esd", "transient voltage", "snubber circuit"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Real-world hardware-software co-debugging, inductive back-EMF protection, and supply rail stability."
            }
        ]
        questions = electronics_bank[:target_count]

    # Domain B: Software Engineering, Web & Fullstack
    elif any(k in prompt_lower for k in ["software", "react", "node", "javascript", "python", "fullstack", "frontend", "backend", "cloud", "aws", "docker", "api"]):
        sw_bank = [
            {
                "category": "Software Architecture",
                "question_text": f"In a modern distributed application handling high concurrency, how do you design scalable service boundaries, state management, and caching strategies? Give an example matching {prompt_text or role}.",
                "expected_keywords": ["microservices", "caching", "redis", "concurrency", "stateless", "load balancing", "horizontal scaling"],
                "time_limit_seconds": 120,
                "evaluation_criteria": "Clarity of distributed systems patterns, database bottleneck awareness, and trade-offs."
            },
            {
                "category": "Database & Data Modeling",
                "question_text": "How do you optimize slow database queries and design schemas for both relational (PostgreSQL/MySQL) and document (MongoDB) databases? How do compound indexes and indexing strategies affect write vs read throughput?",
                "expected_keywords": ["indexing", "query plan", "explain analyze", "normalization", "write throughput", "read replica", "sharding"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Deep database knowledge, B-tree indexes, execution plans, and caching."
            },
            {
                "category": "API Design & Resiliency",
                "question_text": "What design principles do you adhere to when building secure, idempotent RESTful or GraphQL APIs? How do you implement circuit breakers, rate limiting, and graceful degradation during downstream outages?",
                "expected_keywords": ["idempotency", "circuit breaker", "rate limiting", "token bucket", "rest", "graceful degradation", "jwt/oauth"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Production resiliency, API contract design, and security best practices."
            },
            {
                "category": "DevOps & CI/CD",
                "question_text": "Describe your CI/CD pipeline and automated testing methodology. How do you implement canary deployments or blue-green rollouts to ensure zero-downtime releases?",
                "expected_keywords": ["ci/cd", "automated testing", "docker", "canary", "blue-green", "rollback", "observability", "metrics"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Modern DevOps practices, automated test suites (unit/integration), and automated rollback."
            },
            {
                "category": "Production Incident Management",
                "question_text": "Walk us through a critical production bug or outage you diagnosed. What monitoring tools (APM, logs, distributed tracing) did you leverage, and what was your post-mortem prevention plan?",
                "expected_keywords": ["root cause analysis", "apm", "distributed tracing", "post-mortem", "mitigation", "slos", "monitoring"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Analytical composure, observability tools, and preventing recurrence."
            }
        ]
        questions = sw_bank[:target_count]

    # Domain C: Finance, Statutory Tax & Accounts
    elif any(k in prompt_lower for k in ["finance", "account", "gst", "tds", "tax", "audit", "balance sheet", "tally"]):
        fin_bank = [
            {
                "category": "Statutory Tax & GST",
                "question_text": "Explain the reconciliation process between GSTR-1, GSTR-3B, and GSTR-2B. How do you handle input tax credit (ITC) mismatches and invoice reversals?",
                "expected_keywords": ["gstr-1", "gstr-3b", "gstr-2b", "input tax credit", "itc reversal", "reconciliation", "e-invoicing"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Comprehensive understanding of Indian GST compliance, ITC eligibility, and portal filing."
            },
            {
                "category": "TDS & Direct Taxation",
                "question_text": "What are the compliance requirements for Tax Deducted at Source (TDS) under Section 194C, 194J, and 194Q? How do you prepare quarterly Form 26Q filings and handle late payment interest?",
                "expected_keywords": ["section 194c", "194j", "194q", "form 26q", "challan 281", "tan", "interest calculation", "withholding tax"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Direct taxation knowledge, threshold limits, contractor vs professional rates, and timely remittance."
            },
            {
                "category": "Financial Reporting & Balance Sheet",
                "question_text": "Describe your month-end closing procedure. How do you verify prepaid expenses, accrued liabilities, depreciation schedules, and bank reconciliations?",
                "expected_keywords": ["month-end closing", "accrual", "prepaid expenses", "depreciation", "bank reconciliation", "trial balance", "ledger"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Meticulous accounting principles, accrual accounting, and ledger integrity."
            },
            {
                "category": "Cost Control & Internal Audits",
                "question_text": "How do you detect anomalies, duplicate vendor disbursements, or unbudgeted department expenditures during internal audits?",
                "expected_keywords": ["internal audit", "variance analysis", "three-way matching", "purchase order", "cost center", "fraud detection"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Internal controls, three-way matching (PO, GRN, Invoice), and variance reporting."
            },
            {
                "category": "Cash Flow & Capital Budgeting",
                "question_text": "How do you project 12-month working capital requirements and manage cash flow during seasonal fluctuations or delayed client accounts receivable?",
                "expected_keywords": ["working capital", "cash flow forecast", "accounts receivable", "dso", "liquidity", "credit terms"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Cash flow forecasting, DSO management, and liquidity planning."
            }
        ]
        questions = fin_bank[:target_count]

    # Domain D: Custom Prompt Dynamic Synthesis (Universal for ANY prompt entered by HR)
    else:
        topic_clean = prompt_text if prompt_text else role
        # Strip common prompt phrases like "ask questions on", "5 questions on", etc.
        cleaned_topic = re.sub(r'^(?:please\s+)?(?:ask|generate|create|interview)\s+(?:\d+\s+)?(?:questions?\s+(?:on|about|for)?\s*)?', '', topic_clean, flags=re.IGNORECASE).strip()
        if not cleaned_topic:
            cleaned_topic = role

        topic_words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_topic) if w.lower() not in ["the", "and", "for", "with", "questions", "interview"]]
        key_terms = topic_words if topic_words else ["domain principles", "best practices", "execution"]

        custom_templates = [
            {
                "category": f"{cleaned_topic.title()} Fundamentals",
                "question_text": f"What are the foundational principles, core theories, and industry standards essential for mastery in {cleaned_topic}?",
                "expected_keywords": key_terms + ["fundamentals", "standards", "best practices", "methodology"],
                "time_limit_seconds": 120,
                "evaluation_criteria": f"Depth of conceptual understanding and mastery of core {cleaned_topic} frameworks."
            },
            {
                "category": "Problem Solving & Diagnostics",
                "question_text": f"Describe a complex problem or high-stakes challenge you solved in the field of {cleaned_topic}. What diagnostic framework did you use to reach root cause and implement a lasting solution?",
                "expected_keywords": key_terms + ["root cause", "analysis", "troubleshooting", "resolution", "impact"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Analytical methodology, critical thinking under pressure, and sustainable resolution."
            },
            {
                "category": "Tooling, Trade-offs & Architecture",
                "question_text": f"When executing initiatives in {cleaned_topic}, what primary tools, software, or methodologies do you evaluate? How do you balance trade-offs between speed, cost, and long-term quality?",
                "expected_keywords": key_terms + ["trade-offs", "tooling", "quality", "efficiency", "scalability"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Practical discernment in choosing tools, resource optimization, and balancing trade-offs."
            },
            {
                "category": "Risk Mitigation & Quality Assurance",
                "question_text": f"What are the most common points of failure or risks encountered in {cleaned_topic}, and what preventive controls or quality assurance protocols do you institute to avoid them?",
                "expected_keywords": key_terms + ["risk mitigation", "quality assurance", "compliance", "controls", "prevention"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Risk awareness, regulatory/quality compliance, and defensive execution."
            },
            {
                "category": "Execution & Measurable Impact",
                "question_text": f"How do you track performance, benchmark outcomes, and demonstrate quantitative business impact when executing projects in {cleaned_topic}?",
                "expected_keywords": key_terms + ["metrics", "kpis", "roi", "benchmarking", "business impact", "outcomes"],
                "time_limit_seconds": 90,
                "evaluation_criteria": "Data-driven mindset, KPI alignment, and clear articulation of business value."
            }
        ]
        questions = custom_templates[:target_count]

    # Ensure each question has a unique ID and difficulty tag
    formatted_questions = []
    for idx, q in enumerate(questions):
        formatted_questions.append({
            "question_id": f"q_{uuid.uuid4().hex[:8]}",
            "category": q.get("category", "Technical Competency"),
            "question_text": q.get("question_text"),
            "expected_keywords": q.get("expected_keywords", []),
            "time_limit_seconds": q.get("time_limit_seconds", 90),
            "evaluation_criteria": q.get("evaluation_criteria", "Depth of subject matter expertise."),
            "difficulty": difficulty
        })

    return {
        "topic": prompt_text or role,
        "question_count": len(formatted_questions),
        "difficulty": difficulty,
        "questions": formatted_questions
    }

# --- 3. POST /api/recruiter/evaluate-interview ---
@router.post("/evaluate-interview")
async def evaluate_interview(payload: InterviewEvaluateRequest):
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers provided for evaluation")

    from services.evaluator import interview_evaluator

    # Convert Pydantic items to dict
    raw_answers = [
        {
            "question_id": item.question_id,
            "category": item.category,
            "question_text": item.question_text,
            "expected_keywords": item.expected_keywords,
            "candidate_answer": item.candidate_answer
        }
        for item in payload.answers
    ]

    eval_result = interview_evaluator.evaluate_submission(
        target_role=payload.target_role,
        answers=raw_answers
    )

    scored_questions = []
    for item, det in zip(payload.answers, eval_result["detailed_evaluations"]):
        scored_questions.append({
            "question_id": item.question_id,
            "category": item.category,
            "question_text": item.question_text,
            "candidate_answer": item.candidate_answer,
            "ai_score": round(det["score"] / 10.0, 1), # 0.0 - 10.0 scale for individual question
            "ai_feedback": det["feedback"]
        })

    return {
        "questions": scored_questions,
        "summary": {
            "technical_score": eval_result["technical_score"],
            "problem_solving_score": eval_result["problem_solving_score"],
            "communication_score": eval_result["clarity_score"],
            "overall_score": eval_result["overall_score"],
            "recommendation": eval_result["recommendation"],
            "summary_notes": eval_result["ai_summary"],
            "strengths": eval_result["strengths"],
            "concerns": eval_result["concerns"]
        }
    }

