const express = require("express");
const router = express.Router();
const Candidate = require("../models/Candidate");
const aiService = require("../services/aiService");

/* ==========================================================================
   GET /interview/:token — Public Candidate Exam Room
   ========================================================================== */
router.get("/:token", async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const { token } = req.params;
    const candidate = await Candidate.findOne({ interviewToken: token });

    if (!candidate) {
      if (isJson) return res.status(404).json({ error: "Invalid interview token" });
      return res.status(404).render("interview/exam-completed", {
        error: "Invalid or expired interview invitation link. Please contact the hiring team.",
        candidate: null
      });
    }

    // Check expiry
    if (candidate.tokenExpiresAt && new Date() > new Date(candidate.tokenExpiresAt)) {
      candidate.interviewStatus = "EXPIRED";
      await candidate.save();
      if (isJson) return res.status(410).json({ error: "Interview link has expired" });
      return res.status(410).render("interview/exam-completed", {
        error: "This 24-hour interview invitation has expired. Please reach out to HR for a new session.",
        candidate
      });
    }

    // If already completed, show completed view
    if (candidate.interviewStatus === "COMPLETED") {
      if (isJson) return res.json({ status: "COMPLETED", message: "Interview already submitted", candidate });
      return res.render("interview/exam-completed", {
        candidate,
        error: null
      });
    }

    // Mark as IN_PROGRESS if first time opening
    if (candidate.interviewStatus === "INVITED" || candidate.interviewStatus === "PENDING") {
      candidate.interviewStatus = "IN_PROGRESS";
      candidate.interviewStartedAt = new Date();
      await candidate.save();
    }

    if (isJson) {
      return res.json({
        candidateName: candidate.candidateName,
        targetRole: candidate.targetRole,
        department: candidate.department,
        questions: candidate.interviewQuestions
      });
    }

    res.render("interview/exam-portal", {
      candidate,
      questions: candidate.interviewQuestions,
      token
    });
  } catch (err) {
    console.error("[Candidate Portal Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.status(500).send("Error loading candidate exam portal.");
  }
});

/* ==========================================================================
   POST /interview/:token/submit — Submit Answers & Trigger AI Evaluation
   ========================================================================== */
router.post("/:token/submit", async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const { token } = req.params;
    const candidate = await Candidate.findOne({ interviewToken: token });

    if (!candidate) {
      if (isJson) return res.status(404).json({ error: "Invalid interview token" });
      return res.status(404).render("interview/exam-completed", {
        error: "Invalid interview session.",
        candidate: null
      });
    }

    if (candidate.interviewStatus === "COMPLETED") {
      if (isJson) return res.json({ message: "Interview already submitted previously." });
      return res.render("interview/exam-completed", { candidate, error: null });
    }

    // Extract submitted answers from req.body (supports form post answer_{id} or json { answers })
    const submittedAnswers = [];
    candidate.interviewQuestions.forEach((q) => {
      const answerVal = (req.body.answers && req.body.answers[q.questionId]) ||
                        req.body[`answer_${q.questionId}`] ||
                        "";
      q.candidateAnswer = answerVal.trim();
      submittedAnswers.push({
        question_id: q.questionId,
        category: q.category || "General",
        question_text: q.questionText,
        expected_keywords: q.expectedKeywords || [],
        candidate_answer: q.candidateAnswer
      });
    });

    // Call Python AI evaluation service
    try {
      const aiEval = await aiService.evaluateInterviewAI({
        target_role: candidate.targetRole || "SOFTWARE ENGINEER",
        answers: submittedAnswers
      });

      // Update question scores
      if (aiEval.questions && Array.isArray(aiEval.questions)) {
        aiEval.questions.forEach((sc) => {
          const match = candidate.interviewQuestions.find(q => q.questionId === sc.question_id);
          if (match) {
            match.aiScore = sc.ai_score;
            match.aiFeedback = sc.ai_feedback;
          }
        });
      }

      if (aiEval.summary) {
        candidate.aiAssessmentSummary = {
          technicalScore: aiEval.summary.technical_score,
          communicationScore: aiEval.summary.communication_score,
          problemSolvingScore: aiEval.summary.problem_solving_score,
          overallScore: aiEval.summary.overall_score,
          recommendation: aiEval.summary.recommendation,
          summaryNotes: aiEval.summary.summary_notes
        };
        candidate.recommendation = aiEval.summary.recommendation;
      }
    } catch (aiErr) {
      console.warn("[Python AI Evaluation Fallback]:", aiErr.message);
      // Fallback heuristic scoring
      let totalLength = 0;
      candidate.interviewQuestions.forEach(q => {
        totalLength += (q.candidateAnswer || "").length;
        q.aiScore = Math.min(10, Math.max(4, Math.round((q.candidateAnswer || "").length / 20)));
        q.aiFeedback = "Response recorded. Pending HR manual review.";
      });
      const avgScore = Math.min(95, Math.max(50, Math.round(totalLength / 10)));
      candidate.aiAssessmentSummary = {
        technicalScore: avgScore,
        communicationScore: avgScore,
        problemSolvingScore: avgScore,
        overallScore: avgScore,
        recommendation: avgScore >= 70 ? "SHORTLIST" : "HOLD",
        summaryNotes: "Evaluation generated via baseline heuristics."
      };
    }

    candidate.interviewStatus = "COMPLETED";
    candidate.status = "INTERVIEWED";
    candidate.interviewCompletedAt = new Date();
    await candidate.save();

    if (isJson) {
      return res.json({
        success: true,
        message: "Interview completed and evaluated successfully!",
        summary: candidate.aiAssessmentSummary
      });
    }

    res.render("interview/exam-completed", {
      candidate,
      error: null
    });
  } catch (err) {
    console.error("[Interview Submit Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.status(500).send("Error submitting interview.");
  }
});

module.exports = router;
