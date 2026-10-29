const mongoose = require("mongoose");
const createTenantModelProxy = require("../utils/tenantModel");

const candidateSchema = new mongoose.Schema(
  {
    candidateName: {
      type: String,
      required: true,
      trim: true
    },
    email: {
      type: String,
      trim: true,
      lowercase: true,
      default: ""
    },
    phone: {
      type: String,
      trim: true,
      default: ""
    },
    targetRole: {
      type: String,
      required: true,
      trim: true
    },
    department: {
      type: String,
      default: "GENERAL",
      trim: true
    },
    resumeText: {
      type: String,
      default: ""
    },
    resumeFileUrl: {
      type: String,
      default: ""
    },
    matchScore: {
      type: Number,
      default: 0,
      min: 0,
      max: 100
    },
    extractedSkills: [
      {
        type: String,
        trim: true
      }
    ],
    missingSkills: [
      {
        type: String,
        trim: true
      }
    ],
    yearsOfExperience: {
      type: Number,
      default: 0
    },
    education: {
      type: String,
      default: "Not Specified"
    },
    aiSummary: {
      type: String,
      default: ""
    },
    strengths: [
      {
        type: String
      }
    ],
    recommendation: {
      type: String,
      enum: ["STRONG_HIRE", "SHORTLIST", "HOLD", "REJECT"],
      default: "HOLD"
    },
    callImmediately: {
      type: Boolean,
      default: false,
      index: true
    },

    // AI Candidate Exam & Interview Bot Additions
    interviewToken: {
      type: String,
      index: true,
      default: null
    },
    tokenExpiresAt: {
      type: Date,
      default: null
    },
    interviewStatus: {
      type: String,
      enum: ["PENDING", "INVITED", "IN_PROGRESS", "COMPLETED", "EXPIRED"],
      default: "PENDING"
    },
    customBotPrompt: {
      type: String,
      default: ""
    },
    examTopic: {
      type: String,
      default: ""
    },
    difficultyLevel: {
      type: String,
      enum: ["JUNIOR", "MID", "SENIOR", "LEAD"],
      default: "MID"
    },
    questionCount: {
      type: Number,
      default: 5
    },
    interviewStartedAt: Date,
    interviewCompletedAt: Date,
    interviewQuestions: [
      {
        questionId: String,
        category: String, // Technical, Situational, Behavioral, Culture Fit
        questionText: String,
        expectedKeywords: [String],
        timeLimitSeconds: { type: Number, default: 90 },
        candidateAnswer: { type: String, default: "" },
        aiScore: { type: Number, default: 0 },
        aiFeedback: { type: String, default: "" }
      }
    ],
    aiAssessmentSummary: {
      technicalScore: { type: Number, default: 0 },
      communicationScore: { type: Number, default: 0 },
      problemSolvingScore: { type: Number, default: 0 },
      overallScore: { type: Number, default: 0 },
      recommendation: {
        type: String,
        enum: ["STRONG_HIRE", "SHORTLIST", "HOLD", "REJECT"],
        default: "HOLD"
      },
      summaryNotes: { type: String, default: "" }
    },

    status: {
      type: String,
      enum: ["NEW", "INVITED", "SHORTLISTED", "INTERVIEWED", "HIRED", "REJECTED"],
      default: "NEW"
    },
    convertedToEmployeeId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee",
      default: null
    }
  },
  { timestamps: true }
);

module.exports = createTenantModelProxy("Candidate", candidateSchema);
