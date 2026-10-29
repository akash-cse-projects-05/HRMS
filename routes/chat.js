const express = require("express");
const router = express.Router();
const ChatMessage = require("../models/ChatMessage");
const Employee = require("../models/Employee");
const Attendence = require("../models/Attendence");
const chatSocket = require("../services/chatSocket");

/* ==========================================================================
   GET /chat — Main Collaboration & Chat Hub
   ========================================================================== */
router.get("/", async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const currentEmployeeId = req.session.employeeId;
    if (!currentEmployeeId && !req.session.userId) {
      return res.redirect("/auth/login");
    }

    let currentEmployee = null;
    if (currentEmployeeId && currentEmployeeId !== "000000000000000000000000") {
      currentEmployee = await Employee.findById(currentEmployeeId);
    } else if (req.session.role === "HR") {
      currentEmployee = {
        _id: "000000000000000000000000",
        firstName: "HR",
        lastName: "Admin",
        department: "HR",
        designation: "HR Administrator"
      };
    }

    const coworkers = await Employee.find({ status: "Active" }).select("firstName lastName department designation");

    // Standard Department Channels
    const channels = ["general", "engineering", "hr", "accounts", "operations", "sales"];

    // Update current user's presence as AVAILABLE
    if (currentEmployeeId) {
      chatSocket.updateUserPresence(currentEmployeeId, "AVAILABLE");
    }

    if (isJson) {
      return res.json({ channels, coworkers, currentEmployee });
    }

    res.render("chat/index", {
      channels,
      coworkers,
      currentEmployee,
      currentEmployeeId: currentEmployeeId || null
    });
  } catch (err) {
    console.error("[Chat Hub Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.status(500).send("Error loading chat hub.");
  }
});

/* ==========================================================================
   GET /chat/channel/:channelName — Fetch Channel Messages
   ========================================================================== */
router.get("/channel/:channelName", async (req, res) => {
  try {
    const channelName = (req.params.channelName || "general").toLowerCase();
    const messages = await ChatMessage.find({ type: "CHANNEL", channelName })
      .populate("senderId", "firstName lastName designation department profilePicture")
      .sort({ createdAt: 1 })
      .limit(100);

    const formatted = messages.map(m => {
      const doc = m.toObject();
      if (!doc.senderId || doc.senderId._id?.toString() === "000000000000000000000000") {
        doc.senderId = {
          _id: "000000000000000000000000",
          firstName: "HR",
          lastName: "Admin",
          department: "HR",
          designation: "HR Administrator"
        };
      }
      return doc;
    });

    res.json({ success: true, channelName, messages: formatted });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/* ==========================================================================
   GET /chat/direct/:employeeId — Fetch 1-on-1 Direct Message History
   ========================================================================== */
router.get("/direct/:employeeId", async (req, res) => {
  try {
    const currentId = req.session.employeeId;
    const targetId = req.params.employeeId;

    if (!currentId) {
      return res.status(401).json({ error: "Session required" });
    }

    const messages = await ChatMessage.find({
      type: "DIRECT",
      $or: [
        { senderId: currentId, recipientId: targetId },
        { senderId: targetId, recipientId: currentId }
      ]
    })
      .populate("senderId", "firstName lastName designation department")
      .populate("recipientId", "firstName lastName designation department")
      .sort({ createdAt: 1 })
      .limit(100);

    res.json({ success: true, targetId, messages });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/* ==========================================================================
   POST /chat/send — Send Message (Direct or Channel)
   ========================================================================== */
router.post("/send", async (req, res) => {
  try {
    const senderId = req.session.employeeId;
    if (!senderId) {
      return res.status(401).json({ error: "Session required" });
    }

    const { type, channelName, recipientId, messageText, contextCard } = req.body;

    if (!messageText || !messageText.trim()) {
      return res.status(400).json({ error: "Message cannot be empty" });
    }

    const newMsg = new ChatMessage({
      type: type || "CHANNEL",
      channelName: (channelName || "general").toLowerCase(),
      senderId,
      recipientId: type === "DIRECT" ? recipientId : null,
      messageText: messageText.trim(),
      contextCard: contextCard || { cardType: "NONE" },
      attachments: req.body.attachments || [],
      readBy: [senderId]
    });
    await newMsg.save();

    const populated = await ChatMessage.findById(newMsg._id).populate("senderId", "firstName lastName department designation");

    // Refresh presence
    chatSocket.updateUserPresence(senderId, "AVAILABLE");

    res.json({ success: true, message: populated });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/* ==========================================================================
   GET /chat/presence — Fetch Coworker Online & Punch-In Status
   ========================================================================== */
router.get("/presence", async (req, res) => {
  try {
    const online = chatSocket.getAllOnlineUsers();
    res.json({ success: true, online });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
