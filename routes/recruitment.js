const express = require("express");
const router = express.Router();
const multer = require("multer");
const crypto = require("crypto");
const Candidate = require("../models/Candidate");
const Employee = require("../models/Employee");
const User = require("../models/User");
const path = require("path");
const { PDFParse } = require("pdf-parse");
const mammoth = require("mammoth");
const { 
  scrutinizeResume, 
  isResumeDocument, 
  extractEmail, 
  extractPhone, 
  extractCandidateName 
} = require("../utils/resumeScreener");
const aiService = require("../services/aiService");

// HR Authorization Middleware
function hrAuth(req, res, next) {
  if (!req.session.userId || req.session.role !== "HR") {
    const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");
    if (isJson) {
      return res.status(401).json({ error: "Unauthorized. HR session required." });
    }
    return res.redirect("/hr/hr-login");
  }
  next();
}

// Multer in-memory storage configuration for resume file uploads (up to 50 files)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 15 * 1024 * 1024 } // 15MB limit per file
});

/**
 * Robust Text Extractor for PDF, DOCX, and TXT files
 */
async function extractTextFromFile(file) {
  if (!file || !file.buffer) return "";
  const ext = path.extname(file.originalname || "").toLowerCase();
  const mime = file.mimetype || "";

  // 1. PDF Documents
  if (ext === ".pdf" || mime === "application/pdf") {
    try {
      const parser = new PDFParse({ data: file.buffer });
      const result = await parser.getText();
      await parser.destroy();
      if (result && result.text && result.text.trim().length > 0) {
        return result.text.trim();
      }
    } catch (pdfErr) {
      console.warn(`[PDF parsing warning for ${file.originalname}]:`, pdfErr.message);
    }
  }

  // 2. DOCX Documents
  if (ext === ".docx" || mime.includes("wordprocessingml") || mime.includes("officedocument")) {
    try {
      const result = await mammoth.extractRawText({ buffer: file.buffer });
      if (result && result.value && result.value.trim().length > 0) {
        return result.value.trim();
      }
    } catch (docxErr) {
      console.warn(`[DOCX parsing warning for ${file.originalname}]:`, docxErr.message);
    }
  }

  // 3. Plain text / Markdown
  if (ext === ".txt" || ext === ".text" || ext === ".md" || mime.startsWith("text/")) {
    try {
      return file.buffer.toString("utf-8").trim();
    } catch (txtErr) {
      console.warn(`[Text parsing warning for ${file.originalname}]:`, txtErr.message);
    }
  }

  // 4. Fallback UTF-8 string decoding with printable char filtering
  try {
    const raw = file.buffer.toString("utf-8").replace(/[^\x20-\x7E\n]/g, " ").trim();
    return raw;
  } catch (e) {
    return "";
  }
}

/* ==========================================================================
   GET: Recruitment & Resume Screening Dashboard
   ========================================================================== */
router.get("/", hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const candidates = await Candidate.find().sort({ matchScore: -1, createdAt: -1 });

    if (isJson) {
      return res.json({ candidates });
    }

    res.render("hr/resume-screening", {
      candidates,
      success_msg: req.query.success || "",
      error_msg: req.query.error || ""
    });
  } catch (err) {
    console.error("[Recruitment Dashboard Error]:", err);
    if (isJson) return res.status(500).json({ error: "Failed to load candidates" });
    res.status(500).send("Error loading recruitment dashboard.");
  }
});

/* ==========================================================================
   POST: Screen Single or Bulk Resumes with Python AI (Fallback to Local Screener)
   ========================================================================== */
router.post("/screen", hrAuth, upload.array("resumeFiles", 50), async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const { targetRole, department, resumeText, candidateName } = req.body;
    const files = req.files || [];
    const screenedResults = [];
    const skippedFiles = [];

    // Helper function to screen text using Python AI service with fallback
    async function runScreening(text, name, fileName = "Resume") {
      const detectedEmail = extractEmail(text);
      const detectedPhone = extractPhone(text);
      const finalName = name || extractCandidateName(text, fileName);

      try {
        const aiData = await aiService.screenResumeAI({
          resume_text: text,
          target_role: targetRole || "SOFTWARE ENGINEER",
          department: department || "GENERAL",
          candidate_name: finalName
        });

        const isCallImmediately = Boolean(
          aiData.call_immediately ||
          aiData.score >= 80 ||
          aiData.recommendation === "STRONG_HIRE"
        );

        return {
          candidateName: finalName,
          email: aiData.email || detectedEmail || "",
          phone: aiData.phone || detectedPhone || "",
          targetRole: targetRole || "SOFTWARE ENGINEER",
          department: department || "GENERAL",
          matchScore: aiData.score || 0,
          extractedSkills: aiData.matched_skills || [],
          missingSkills: aiData.missing_skills || [],
          yearsOfExperience: aiData.experience_years || 0,
          recommendation: aiData.recommendation || "HOLD",
          callImmediately: isCallImmediately,
          strengths: aiData.strengths || [],
          aiSummary: aiData.summary || ""
        };
      } catch (aiErr) {
        console.warn("[Python AI Unavailable, using local fallback]:", aiErr.message);
        const localResult = await scrutinizeResume({
          resumeText: text,
          targetRole: targetRole || "SOFTWARE ENGINEER",
          candidateName: finalName,
          fileName
        });

        const isCallImmediately = Boolean(
          localResult.callImmediately ||
          localResult.matchScore >= 80 ||
          localResult.recommendation === "STRONG_HIRE"
        );

        return {
          ...localResult,
          candidateName: finalName,
          email: localResult.email || detectedEmail || "",
          phone: localResult.phone || detectedPhone || "",
          callImmediately: isCallImmediately
        };
      }
    }

    // 1. Process Raw Text input if provided
    if (resumeText && resumeText.trim().length > 0) {
      const cleanText = resumeText.trim();
      if (!isResumeDocument(cleanText)) {
        const msg = "The entered text does not appear to be a candidate resume (missing standard resume sections like experience, skills, education, or contact info). Only valid resumes can be screened.";
        if (isJson) return res.status(400).json({ error: msg });
        return res.redirect(`/hr/recruitment?error=${encodeURIComponent(msg)}`);
      }

      const result = await runScreening(cleanText, candidateName);
      const candidate = new Candidate({
        ...result,
        department: department || "GENERAL",
        resumeText: cleanText
      });
      await candidate.save();
      screenedResults.push(candidate);
    }

    // 2. Process Uploaded Files in Bulk (PDF, DOCX, TXT)
    for (const file of files) {
      const ext = path.extname(file.originalname).toLowerCase();
      // Only allow PDF, DOCX, DOC, TXT
      if (![".pdf", ".docx", ".doc", ".txt", ".text"].includes(ext)) {
        skippedFiles.push(`${file.originalname} (Unsupported file format: only PDF, DOCX, and TXT resumes are allowed)`);
        continue;
      }

      const fileText = await extractTextFromFile(file);
      if (!fileText || fileText.length < 40) {
        skippedFiles.push(`${file.originalname} (Empty or unreadable document content)`);
        continue;
      }

      // Resume document verification - ONLY genuine resumes are screened!
      if (!isResumeDocument(fileText)) {
        skippedFiles.push(`${file.originalname} (Document does not contain candidate resume structures like experience, skills, or contact info)`);
        continue;
      }

      const result = await runScreening(fileText, candidateName, file.originalname);
      const candidate = new Candidate({
        ...result,
        department: department || "GENERAL",
        resumeText: fileText,
        resumeFileUrl: `/uploads/${file.originalname}`
      });
      await candidate.save();
      screenedResults.push(candidate);
    }

    if (screenedResults.length === 0) {
      let msg = "No valid resumes were found to screen.";
      if (skippedFiles.length > 0) {
        msg = `No valid resumes found. Filtered out: ${skippedFiles.join("; ")}`;
      }
      if (isJson) return res.status(400).json({ error: msg, skippedFiles });
      return res.redirect(`/hr/recruitment?error=${encodeURIComponent(msg)}`);
    }

    let successMsg = `Successfully screened ${screenedResults.length} candidate resume(s)!`;
    const readyToCallCount = screenedResults.filter(c => c.callImmediately).length;
    if (readyToCallCount > 0) {
      successMsg += ` 🎯 ${readyToCallCount} top candidate(s) flagged ready for immediate call & recruitment.`;
    }
    if (skippedFiles.length > 0) {
      successMsg += ` (${skippedFiles.length} non-resume files were skipped).`;
    }

    if (isJson) {
      return res.json({
        success: true,
        message: successMsg,
        screenedResults,
        skippedFiles
      });
    }

    res.redirect(`/hr/recruitment?success=${encodeURIComponent(successMsg)}`);
  } catch (err) {
    console.error("[Resume Screening Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.redirect(`/hr/recruitment?error=${encodeURIComponent(err.message)}`);
  }
});

/* ==========================================================================
   POST: Generate 24h AI Interview Invite & Dynamic Role Questions as per HR Prompt
   ========================================================================== */
router.post("/:id/invite", hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const candidate = await Candidate.findById(req.params.id);
    if (!candidate) {
      if (isJson) return res.status(404).json({ error: "Candidate not found" });
      return res.redirect("/hr/recruitment?error=Candidate+not+found");
    }

    const prompt = (req.body.prompt || req.body.customBotPrompt || "").trim();
    const questionCount = parseInt(req.body.questionCount || req.body.question_count) || 5;
    const difficulty = (req.body.difficulty || "MID").toUpperCase();

    // Generate single-use, 24h temporary token
    const token = crypto.randomBytes(16).toString("hex");
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours

    // Generate dynamic interview questions via Python AI service
    let questions = [];
    let generatedTopic = candidate.targetRole;
    try {
      const aiResponse = await aiService.generateInterviewQuestionsAI({
        target_role: candidate.targetRole || "GENERAL",
        prompt: prompt || candidate.targetRole,
        skills: candidate.extractedSkills || [],
        department: candidate.department || "GENERAL",
        question_count: questionCount,
        difficulty: difficulty
      });
      generatedTopic = aiResponse.topic || prompt || candidate.targetRole;
      questions = (aiResponse.questions || []).map((q) => ({
        questionId: q.question_id,
        category: q.category,
        questionText: q.question_text,
        expectedKeywords: q.expected_keywords,
        timeLimitSeconds: q.time_limit_seconds || 90,
        candidateAnswer: "",
        aiScore: 0,
        aiFeedback: ""
      }));
    } catch (aiErr) {
      console.warn("[AI Question Generation Fallback]:", aiErr.message);
      questions = [
        {
          questionId: "q_1",
          category: "Technical Competency",
          questionText: `Describe your hands-on technical architecture and engineering methodology for ${prompt || candidate.targetRole}.`,
          expectedKeywords: ["architecture", "scaling", "clean code", "testing"],
          timeLimitSeconds: 120,
          candidateAnswer: "",
          aiScore: 0
        },
        {
          questionId: "q_2",
          category: "Situational",
          questionText: "How do you handle critical failures or defect troubleshooting under tight deadlines while collaborating with stakeholders?",
          expectedKeywords: ["root cause", "post-mortem", "prioritization", "communication"],
          timeLimitSeconds: 90,
          candidateAnswer: "",
          aiScore: 0
        }
      ];
    }

    candidate.customBotPrompt = prompt;
    candidate.examTopic = generatedTopic;
    candidate.difficultyLevel = difficulty;
    candidate.questionCount = questions.length;
    candidate.interviewToken = token;
    candidate.tokenExpiresAt = expiresAt;
    candidate.interviewStatus = "INVITED";
    candidate.status = "INVITED";
    candidate.interviewQuestions = questions;
    await candidate.save();

    const inviteLink = `${req.protocol}://${req.get("host")}/interview/${token}`;

    if (isJson) {
      return res.json({
        success: true,
        message: `AI Interview Bot configured with ${questions.length} questions on "${generatedTopic}"!`,
        inviteLink,
        token,
        expiresAt,
        topic: generatedTopic,
        questionsCount: questions.length
      });
    }

    res.redirect(`/hr/recruitment?success=Generated+AI+Interview+Bot+Link:+${encodeURIComponent(inviteLink)}`);
  } catch (err) {
    console.error("[Interview Invite Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.redirect(`/hr/recruitment?error=${encodeURIComponent(err.message)}`);
  }
});

/* ==========================================================================
   POST: Instant Create AI Exam Bot (Standalone Prompt & Candidate Setup)
   ========================================================================== */
router.post("/create-exam-bot", hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const { candidateName, email, targetRole, department, prompt, questionCount, difficulty } = req.body;
    const cleanName = (candidateName || "Candidate").trim();
    const cleanRole = (targetRole || prompt || "Specialist").trim();
    const qCount = parseInt(questionCount) || 5;
    const diff = (difficulty || "MID").toUpperCase();
    const botPrompt = (prompt || cleanRole).trim();

    // Call Python AI Service with prompt
    const aiResponse = await aiService.generateInterviewQuestionsAI({
      target_role: cleanRole,
      prompt: botPrompt,
      department: department || "GENERAL",
      question_count: qCount,
      difficulty: diff
    });

    const questions = (aiResponse.questions || []).map((q) => ({
      questionId: q.question_id,
      category: q.category,
      questionText: q.question_text,
      expectedKeywords: q.expected_keywords,
      timeLimitSeconds: q.time_limit_seconds || 90,
      candidateAnswer: "",
      aiScore: 0,
      aiFeedback: ""
    }));

    const token = crypto.randomBytes(16).toString("hex");
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000);

    const candidate = new Candidate({
      candidateName: cleanName,
      email: (email || "").trim(),
      targetRole: cleanRole,
      department: department || "GENERAL",
      customBotPrompt: botPrompt,
      examTopic: aiResponse.topic || botPrompt || cleanRole,
      difficultyLevel: diff,
      questionCount: questions.length,
      interviewToken: token,
      tokenExpiresAt: expiresAt,
      interviewStatus: "INVITED",
      status: "INVITED",
      interviewQuestions: questions,
      aiSummary: `AI Exam Bot configured for topic: "${botPrompt}" with ${questions.length} questions.`
    });

    await candidate.save();
    const inviteLink = `${req.protocol}://${req.get("host")}/interview/${token}`;

    if (isJson) {
      return res.json({
        success: true,
        message: `AI Exam Bot generated with ${questions.length} questions on "${aiResponse.topic || botPrompt}"`,
        inviteLink,
        token,
        candidateId: candidate._id,
        topic: candidate.examTopic,
        questionsCount: questions.length
      });
    }

    res.redirect(`/hr/recruitment?success=Created+AI+Exam+Bot+Link:+${encodeURIComponent(inviteLink)}`);
  } catch (err) {
    console.error("[Create Exam Bot Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.redirect(`/hr/recruitment?error=${encodeURIComponent(err.message)}`);
  }
});

/* ==========================================================================
   GET: Candidate AI Interview Evaluation Scorecard Report
   ========================================================================== */
router.get("/:id/report", hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const candidate = await Candidate.findById(req.params.id);
    if (!candidate) {
      if (isJson) return res.status(404).json({ error: "Candidate not found" });
      return res.redirect("/hr/recruitment?error=Candidate+not+found");
    }

    if (isJson) {
      return res.json({ candidate });
    }

    res.render("hr/candidate-report", {
      candidate,
      success_msg: req.query.success || "",
      error_msg: req.query.error || ""
    });
  } catch (err) {
    console.error("[Candidate Report Error]:", err);
    if (isJson) return res.status(500).json({ error: "Failed to load candidate report" });
    res.status(500).send("Error loading evaluation report.");
  }
});

/* ==========================================================================
   POST: 1-Click Convert Candidate to Active Employee
   ========================================================================== */
router.post(["/:id/convert", "/candidate/:id/convert"], hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const candidate = await Candidate.findById(req.params.id);
    if (!candidate) {
      if (isJson) return res.status(404).json({ error: "Candidate not found" });
      return res.redirect("/hr/recruitment?error=Candidate+not+found");
    }

    if (candidate.status === "HIRED" && candidate.convertedToEmployeeId) {
      if (isJson) return res.status(400).json({ error: "Candidate is already onboarded as an employee." });
      return res.redirect("/hr/recruitment?error=Candidate+is+already+onboarded.");
    }

    const nameParts = candidate.candidateName.trim().split(" ");
    const firstName = nameParts[0] || "Candidate";
    const lastName = nameParts.slice(1).join(" ") || "Employee";
    const empCode = "EMP" + Math.floor(1000 + Math.random() * 9000);

    const newEmp = new Employee({
      employeeCode: empCode,
      firstName,
      lastName,
      dob: new Date("1995-01-01"),
      email: candidate.email || `${empCode.toLowerCase()}@rsraviation.com`,
      phoneNumber: candidate.phone || "0000000000",
      department: candidate.department || "GENERAL",
      designation: candidate.targetRole || "STAFF",
      employmentType: "Full-Time",
      joiningDate: new Date(),
      status: "Active",
      createdByHR: true
    });
    await newEmp.save();

    const defaultPassword = "ChangeMe@123";
    const newUser = new User({
      employeeId: newEmp._id,
      username: empCode,
      password: defaultPassword,
      isFirstLogin: true
    });
    await newUser.save();

    candidate.status = "HIRED";
    candidate.convertedToEmployeeId = newEmp._id;
    await candidate.save();

    if (isJson) {
      return res.json({
        success: true,
        message: `Successfully onboarded candidate ${candidate.candidateName} as Employee '${empCode}'!`,
        employee: newEmp,
        loginUsername: empCode,
        loginPassword: defaultPassword
      });
    }

    res.redirect(`/hr/recruitment?success=Candidate+'${candidate.candidateName}'+onboarded+successfully+as+'${empCode}'!`);
  } catch (err) {
    console.error("[Candidate Conversion Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.redirect(`/hr/recruitment?error=${encodeURIComponent(err.message)}`);
  }
});

module.exports = router;
