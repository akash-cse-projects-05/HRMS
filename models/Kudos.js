const mongoose = require("mongoose");
const createTenantModelProxy = require("../utils/tenantModel");

const kudosSchema = new mongoose.Schema(
  {
    senderId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee",
      required: true
    },
    receiverId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee",
      required: true
    },
    badge: {
      type: String,
      enum: ["INNOVATOR", "TEAM_PLAYER", "IMPACT_PLAYER", "PROBLEM_SOLVER", "LEADERSHIP"],
      required: true
    },
    message: {
      type: String,
      required: true,
      maxlength: 500,
      trim: true
    },
    department: {
      type: String,
      default: "GENERAL"
    },
    reactions: [
      {
        employeeId: {
          type: mongoose.Schema.Types.ObjectId,
          ref: "Employee"
        },
        type: {
          type: String,
          enum: ["heart", "clap", "celebrate"]
        }
      }
    ]
  },
  { timestamps: true }
);

module.exports = createTenantModelProxy("Kudos", kudosSchema);
