const mongoose = require("mongoose");
const createTenantModelProxy = require("../utils/tenantModel");

const chatMessageSchema = new mongoose.Schema(
  {
    type: {
      type: String,
      enum: ["DIRECT", "CHANNEL"],
      required: true
    },
    channelName: {
      type: String,
      default: "general",
      trim: true,
      lowercase: true
    }, // e.g. 'general', 'engineering', 'hr', 'accounts', 'operations'
    senderId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee",
      required: true
    },
    recipientId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Employee",
      default: null
    }, // (if DIRECT)
    messageText: {
      type: String,
      required: true,
      trim: true
    },
    contextCard: {
      cardType: {
        type: String,
        enum: ["NONE", "PAYSLIP", "TICKET", "LEAVE", "TIMESHEET"],
        default: "NONE"
      },
      title: String,
      subtitle: String,
      referenceId: String,
      actionUrl: String
    },
    attachments: [
      {
        fileName: String,
        fileUrl: String,
        fileType: String
      }
    ],
    reactions: [
      {
        employeeId: {
          type: mongoose.Schema.Types.ObjectId,
          ref: "Employee"
        },
        emoji: String
      }
    ],
    readBy: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Employee"
      }
    ]
  },
  { timestamps: true }
);

module.exports = createTenantModelProxy("ChatMessage", chatMessageSchema);
