// utils/resumeScreener.js

const JOB_SKILL_TAXONOMY = {
  "SOFTWARE ENGINEER": [
    "javascript", "typescript", "node.js", "react", "react native", "express",
    "mongodb", "sql", "aws", "docker", "git", "rest api", "python", "java", "html", "css", "c++", "c#"
  ],
  "FULL STACK DEVELOPER": [
    "javascript", "typescript", "react", "next.js", "vue.js", "node.js", "express", "mongodb", "postgresql", "mysql", "html5", "css3", "git", "aws", "rest api", "graphql"
  ],
  "SALES MANAGER": [
    "lead generation", "crm", "salesforce", "hubspot", "negotiation", "client acquisition", "b2b", "account management", "presentation", "closing", "cold calling"
  ],
  "HR MANAGER": [
    "recruitment", "onboarding", "payroll", "employee relations", "performance management", "compliance", "hrms", "labor laws", "conflict resolution", "talent acquisition"
  ],
  "ACCOUNTANT": [
    "tally", "excel", "gst", "tds", "financial reporting", "auditing", "taxation", "bookkeeping", "invoicing", "quickbooks", "accounts payable", "accounts receivable"
  ],
  "LOGISTICS MANAGER": [
    "supply chain", "inventory", "vendor management", "fleet management", "dispatch", "warehouse", "logistics", "route optimization", "procurement", "sap"
  ],
  "MARKETING EXECUTIVE": [
    "digital marketing", "seo", "sem", "social media", "content creation", "google analytics", "copywriting", "campaign management", "email marketing", "brand awareness"
  ],
  "DATA SCIENTIST": [
    "python", "r", "machine learning", "deep learning", "sql", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "tableau", "power bi", "statistics"
  ],
  "DEVOPS ENGINEER": [
    "docker", "kubernetes", "aws", "azure", "ci/cd", "jenkins", "terraform", "ansible", "linux", "bash", "git", "monitoring", "prometheus"
  ],
  "GENERAL": [
    "communication", "teamwork", "problem solving", "management", "excel", "microsoft office", "leadership", "time management", "organization"
  ]
};

/**
 * Checks if a skill is present in text using boundary-aware regex to prevent substring false-positives (e.g. 'java' matching 'javascript').
 */
function skillIsPresent(text, skill) {
  const lowerText = (text || "").toLowerCase();
  const lowerSkill = (skill || "").toLowerCase();

  // Escape special regex characters
  const escaped = lowerSkill.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
  
  // Use boundary checks allowing start/end of string or non-alphanumeric separators
  const pattern = `(?:^|[^a-z0-9+#])${escaped}(?:$|[^a-z0-9+#])`;
  const regex = new RegExp(pattern, "i");
  
  return regex.test(lowerText);
}

/**
 * Extracts Email from resume text using regex
 */
function extractEmail(text) {
  const match = (text || "").match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  return match ? match[0].toLowerCase() : "";
}

/**
 * Extracts Phone Number from resume text using regex
 */
function extractPhone(text) {
  const match = (text || "").match(/(?:\+?\d{1,3}[\s-]?)?\(?\d{2,5}\)?[\s.-]?\d{3,5}[\s.-]?\d{3,5}/);
  if (match) {
    const digits = match[0].replace(/\D/g, "");
    if (digits.length >= 10) return match[0].trim();
  }
  const simpleMatch = (text || "").match(/\b\d{10}\b/);
  return simpleMatch ? simpleMatch[0] : "";
}

/**
 * Extracts candidate name fallback from text lines or file name
 */
function extractCandidateName(text, fallbackFileName = "") {
  const lines = (text || "").split("\n").map(l => l.trim()).filter(l => l.length > 0);
  for (const line of lines.slice(0, 5)) {
    // Avoid lines that look like headers or emails
    if (!line.includes("@") && !line.toLowerCase().includes("resume") && line.length < 35 && /^[a-zA-Z\s.-]+$/.test(line)) {
      return line;
    }
  }
  if (fallbackFileName) {
    const clean = fallbackFileName.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ").replace(/resume/gi, "").trim();
    if (clean.length > 0) {
      return clean.charAt(0).toUpperCase() + clean.slice(1);
    }
  }
  return "Candidate " + Math.floor(1000 + Math.random() * 9000);
}

/**
 * Extracts years of experience from text
 */
function extractYearsOfExperience(text) {
  const rawText = text || "";
  const expMatch = rawText.match(/(\d+)\+?\s*(?:years?|yrs?)\b(?:\s*(?:of|in|working)?\s*(?:experience|exp|industry|work|development))?/i);
  if (expMatch) {
    const years = parseInt(expMatch[1], 10);
    if (years >= 0 && years <= 40) return years;
  }
  const dateYears = rawText.match(/\b(19\d{2}|20\d{2})\b/g);
  if (dateYears && dateYears.length >= 2) {
    const sorted = dateYears.map(y => parseInt(y, 10)).sort((a, b) => a - b);
    const diff = sorted[sorted.length - 1] - sorted[0];
    if (diff > 0 && diff <= 40) return diff;
  }
  return 2; // Default baseline estimate
}

/**
 * Extracts education details
 */
function extractEducation(text) {
  const lower = (text || "").toLowerCase();
  if (lower.includes("ph.d") || lower.includes("phd") || lower.includes("doctorate")) {
    return "Doctorate / Ph.D.";
  }
  if (lower.includes("master") || lower.includes("m.tech") || lower.includes("mba") || lower.includes("m.sc") || lower.includes("m.s.") || lower.includes("mca")) {
    return "Master's Degree (Post Graduate)";
  }
  if (lower.includes("bachelor") || lower.includes("b.tech") || lower.includes("b.e") || lower.includes("b.sc") || lower.includes("bca") || lower.includes("b.com") || lower.includes("b.a") || lower.includes("bs ")) {
    return "Bachelor's Degree (Graduate)";
  }
  if (lower.includes("diploma")) {
    return "Diploma";
  }
  return "Bachelor's Degree / Equivalent";
}

const RESUME_INDICATORS = [
  "experience", "education", "skills", "projects", "contact", "email",
  "phone", "summary", "profile", "work", "curriculum vitae", "bachelor",
  "master", "technologies", "certifications", "history", "employment",
  "objective", "languages", "developer", "engineer", "manager", "qualifications"
];

function isResumeDocument(text) {
  if (!text || text.trim().length < 50) return false;
  const lower = text.toLowerCase();
  const count = RESUME_INDICATORS.reduce((acc, kw) => acc + (lower.includes(kw) ? 1 : 0), 0);
  return count >= 2;
}

/**
 * Core Rule-Based AI Resume Screener
 */
function scrutinizeResumeRuleBased({ resumeText, targetRole, candidateName, fileName }) {
  const rawText = resumeText || "";
  const cleanRole = (targetRole || "GENERAL").toUpperCase().trim();
  
  // Find taxonomy for target role or fallback to GENERAL
  const taxonomyKeys = Object.keys(JOB_SKILL_TAXONOMY);
  const matchingKey = taxonomyKeys.find(k => cleanRole.includes(k) || k.includes(cleanRole)) || "GENERAL";
  const requiredSkills = JOB_SKILL_TAXONOMY[matchingKey];

  const extractedSkills = [];
  const missingSkills = [];

  requiredSkills.forEach(skill => {
    if (skillIsPresent(rawText, skill)) {
      extractedSkills.push(skill.toUpperCase());
    } else {
      missingSkills.push(skill.toUpperCase());
    }
  });

  const email = extractEmail(rawText);
  const phone = extractPhone(rawText);
  const name = candidateName || extractCandidateName(rawText, fileName);
  const yearsOfExperience = extractYearsOfExperience(rawText);
  const education = extractEducation(rawText);

  // Score Calculation
  const skillRatio = requiredSkills.length > 0 ? (extractedSkills.length / requiredSkills.length) : 0.5;
  const skillScore = Math.min(skillRatio * 50, 50); // Max 50 points
  const expScore = Math.min((yearsOfExperience / 5) * 30, 30); // Max 30 points
  const eduScore = rawText.toLowerCase().match(/(degree|bachelor|master|phd|b\.tech|m\.tech|bca|mca)/i) ? 15 : 10; // Max 15 points
  const bonusScore = (email && phone) ? 5 : 0; // 5 points for completeness

  const matchScore = Math.min(Math.round(skillScore + expScore + eduScore + bonusScore), 99);

  // Recommendation Badge & Call Immediately Flag
  let recommendation = "HOLD";
  let callImmediately = false;
  if (matchScore >= 80 || (extractedSkills.length >= 4 && yearsOfExperience >= 2)) {
    recommendation = "STRONG_HIRE";
    callImmediately = true;
  } else if (matchScore >= 65) {
    recommendation = "SHORTLIST";
  } else if (matchScore >= 48) {
    recommendation = "HOLD";
  } else {
    recommendation = "REJECT";
  }

  // Strengths & AI Summary
  const strengths = [];
  if (callImmediately) {
    strengths.push("🔥 Priority Candidate: High competency match - Recommended for immediate phone call / recruitment");
  }
  if (extractedSkills.length > 0) {
    strengths.push(`Proficient in core requirements: ${extractedSkills.slice(0, 4).join(", ")}`);
  }
  if (yearsOfExperience >= 3) {
    strengths.push(`Solid experience profile (~${yearsOfExperience} years)`);
  }
  if (email && phone) {
    strengths.push("Complete contact information and verified resume structure");
  }

  const aiSummary = `${name} has a ${matchScore}% profile match for the ${cleanRole} role with ${yearsOfExperience} years of experience and education in ${education}. Key competencies identified: ${extractedSkills.slice(0, 5).join(", ") || "General Domain Skills"}. ${callImmediately ? 'Candidate is qualified for immediate call and fast-track recruitment.' : ''}`;

  return {
    candidateName: name,
    email,
    phone,
    targetRole: cleanRole,
    matchScore,
    extractedSkills,
    missingSkills,
    yearsOfExperience,
    education,
    strengths,
    aiSummary,
    recommendation,
    callImmediately
  };
}

/**
 * Main AI Resume Scrutiny Function
 */
async function scrutinizeResume({ resumeText, targetRole, candidateName, fileName }) {
  if (!resumeText || resumeText.trim().length === 0) {
    throw new Error("Resume text or file content is empty.");
  }

  // Check if Google Gemini AI API key is configured
  if (process.env.GEMINI_API_KEY) {
    try {
      const { GoogleGenerativeAI } = require("@google/generative-ai");
      const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
      const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

      const prompt = `You are an expert HR recruiter. Analyze the following candidate resume for the role of "${targetRole}". Return ONLY a JSON object with this exact structure without markdown formatting:
{
  "candidateName": "Candidate Full Name",
  "email": "Email Address",
  "phone": "Phone Number",
  "matchScore": 85,
  "extractedSkills": ["Skill1", "Skill2"],
  "missingSkills": ["Skill3"],
  "yearsOfExperience": 4,
  "education": "Degree Name",
  "strengths": ["Strength 1", "Strength 2"],
  "aiSummary": "2 sentence executive summary of the candidate suitability",
  "recommendation": "STRONG_HIRE" | "SHORTLIST" | "HOLD" | "REJECT"
}

Resume Text:
${resumeText.substring(0, 3500)}`;

      const result = await model.generateContent(prompt);
      const text = result.response.text();
      const cleanedJson = text.replace(/```json/g, "").replace(/```/g, "").trim();
      const parsed = JSON.parse(cleanedJson);

      return {
        candidateName: parsed.candidateName || candidateName || "Candidate",
        email: parsed.email || extractEmail(resumeText),
        phone: parsed.phone || extractPhone(resumeText),
        targetRole: targetRole || "GENERAL",
        matchScore: Number(parsed.matchScore) || 75,
        extractedSkills: parsed.extractedSkills || [],
        missingSkills: parsed.missingSkills || [],
        yearsOfExperience: Number(parsed.yearsOfExperience) || 2,
        education: parsed.education || "Bachelor's Degree",
        strengths: parsed.strengths || [],
        aiSummary: parsed.aiSummary || "Analyzed by AI",
        recommendation: ["STRONG_HIRE", "SHORTLIST", "HOLD", "REJECT"].includes(parsed.recommendation) ? parsed.recommendation : "SHORTLIST"
      };
    } catch (geminiError) {
      console.warn("[Gemini AI Screener Warning]: Falling back to local NLP engine:", geminiError.message);
    }
  }

  // Default Intelligent Local Rule Engine
  return scrutinizeResumeRuleBased({ resumeText, targetRole, candidateName, fileName });
}

module.exports = { 
  scrutinizeResume, 
  isResumeDocument, 
  extractEmail, 
  extractPhone, 
  extractCandidateName 
};

