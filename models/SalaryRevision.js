const mongoose = require("mongoose");
const createTenantModelProxy = require("../utils/tenantModel");

const salaryRevisionSchema = new mongoose.Schema(
  {
    employeeId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee",
      required: true
    },
    effectiveDate: {
      type: Date,
      required: true
    },
    revisionType: {
      type: String,
      enum: ["Annual Increment", "Promotion", "Market Correction", "Special Adjustment"],
      default: "Annual Increment"
    },
    previousDesignation: {
      type: String,
      default: ""
    },
    newDesignation: {
      type: String,
      default: ""
    },
    previousSalary: {
      type: Number,
      required: true
    }, // Monthly gross/basic
    newSalary: {
      type: Number,
      required: true
    },
    hikePercentage: {
      type: Number,
      required: true
    },

    // Revised Component Breakdown
    breakdown: {
      basicSalary: { type: Number, default: 0 },
      hra: { type: Number, default: 0 },
      travelAllowance: { type: Number, default: 0 },
      specialAllowance: { type: Number, default: 0 },
      otherAllowances: { type: Number, default: 0 },
      pf: { type: Number, default: 0 },
      gratuity: { type: Number, default: 0 },
      professionalTax: { type: Number, default: 200 },
      netPay: { type: Number, default: 0 }
    },
    reason: {
      type: String,
      default: ""
    },
    status: {
      type: String,
      enum: ["PROPOSED", "APPROVED", "APPLIED", "REJECTED"],
      default: "PROPOSED"
    },
    proposedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee"
    },
    approvedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee"
    },
    approvalDate: Date,
    letterGenerated: {
      type: Boolean,
      default: false
    }
  },
  { timestamps: true }
);

module.exports = createTenantModelProxy("SalaryRevision", salaryRevisionSchema);
