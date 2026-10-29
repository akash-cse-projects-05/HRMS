const mongoose = require("mongoose");
const createTenantModelProxy = require("../utils/tenantModel");

const policyDocumentSchema = new mongoose.Schema(
  {
    title: {
      type: String,
      required: true,
      trim: true
    },
    category: {
      type: String,
      enum: ["Leave & Attendance", "Travel & Expense", "Security & IT", "Code of Conduct", "Health & Benefits", "General"],
      default: "General"
    },
    section: {
      type: String,
      default: "General Clause"
    },
    content: {
      type: String,
      required: true
    },
    fileUrl: {
      type: String,
      default: ""
    },
    fileName: {
      type: String,
      default: ""
    },
    fileSize: {
      type: Number,
      default: 0
    },
    pageCount: {
      type: Number,
      default: 1
    },
    chunksCount: {
      type: Number,
      default: 1
    },
    documentId: {
      type: String,
      default: ""
    },
    status: {
      type: String,
      enum: ["INDEXED", "PROCESSING", "FAILED"],
      default: "INDEXED"
    },
    uploadedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee"
    },
    effectiveDate: {
      type: Date,
      default: Date.now
    },
    isActive: {
      type: Boolean,
      default: true
    }
  },
  { timestamps: true }
);

policyDocumentSchema.index({ title: "text", content: "text", section: "text" });
policyDocumentSchema.index({ category: 1, createdAt: -1 });

module.exports = createTenantModelProxy("PolicyDocument", policyDocumentSchema);
