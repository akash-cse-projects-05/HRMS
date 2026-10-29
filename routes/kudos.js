const express = require("express");
const router = express.Router();
const Kudos = require("../models/Kudos");
const Employee = require("../models/Employee");

/* ==========================================================================
   GET /kudos/feed — Celebrations & Kudos Social Wall
   ========================================================================== */
router.get("/feed", async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const kudosList = await Kudos.find()
      .populate("senderId", "firstName lastName designation department profilePicture")
      .populate("receiverId", "firstName lastName designation department profilePicture")
      .sort({ createdAt: -1 })
      .limit(50);

    const activeEmployees = await Employee.find({ status: "Active" }).select("firstName lastName department designation dob joiningDate");

    // Compute today's birthdays and milestone work anniversaries
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentDay = today.getDate();

    const birthdaysToday = activeEmployees.filter((emp) => {
      if (!emp.dob) return false;
      const d = new Date(emp.dob);
      return d.getMonth() === currentMonth && d.getDate() === currentDay;
    });

    const anniversariesToday = activeEmployees.filter((emp) => {
      if (!emp.joiningDate) return false;
      const d = new Date(emp.joiningDate);
      const isSameDate = d.getMonth() === currentMonth && d.getDate() === currentDay;
      const yearsCompleted = today.getFullYear() - d.getFullYear();
      return isSameDate && yearsCompleted > 0;
    }).map(emp => ({
      ...emp.toObject(),
      years: today.getFullYear() - new Date(emp.joiningDate).getFullYear()
    }));

    if (isJson) {
      return res.json({ kudosList, birthdaysToday, anniversariesToday, employees: activeEmployees });
    }

    res.render("kudos/feed", {
      kudosList,
      birthdaysToday,
      anniversariesToday,
      employees: activeEmployees,
      currentEmployeeId: req.session.employeeId || null,
      success_msg: req.query.success || "",
      error_msg: req.query.error || ""
    });
  } catch (err) {
    console.error("[Kudos Feed Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.status(500).send("Error loading celebrations hub.");
  }
});

/* ==========================================================================
   POST /kudos/send — Award Recognition Badge & Message
   ========================================================================== */
router.post("/send", async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const { receiverId, badge, message } = req.body;
    const senderId = req.session.employeeId;

    if (!senderId) {
      if (isJson) return res.status(401).json({ error: "Session required to give kudos" });
      return res.redirect("/auth/login");
    }

    if (!receiverId || !badge || !message) {
      const msg = "Please select a coworker, badge, and message.";
      if (isJson) return res.status(400).json({ error: msg });
      return res.redirect(`/kudos/feed?error=${encodeURIComponent(msg)}`);
    }

    if (String(senderId) === String(receiverId)) {
      const msg = "You cannot award kudos to yourself!";
      if (isJson) return res.status(400).json({ error: msg });
      return res.redirect(`/kudos/feed?error=${encodeURIComponent(msg)}`);
    }

    const receiver = await Employee.findById(receiverId);
    const kudos = new Kudos({
      senderId,
      receiverId,
      badge: badge.toUpperCase(),
      message: message.trim(),
      department: receiver ? receiver.department : "GENERAL",
      reactions: []
    });
    await kudos.save();

    if (isJson) {
      return res.json({ success: true, message: "Kudos awarded successfully!", kudos });
    }

    res.redirect("/kudos/feed?success=Kudos+awarded+successfully!");
  } catch (err) {
    console.error("[Give Kudos Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.redirect(`/kudos/feed?error=${encodeURIComponent(err.message)}`);
  }
});

/* ==========================================================================
   POST /kudos/:id/react — React with heart, clap, or celebrate
   ========================================================================== */
router.post("/:id/react", async (req, res) => {
  try {
    const { type } = req.body; // "heart", "clap", "celebrate"
    const employeeId = req.session.employeeId;

    if (!employeeId) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    const kudos = await Kudos.findById(req.params.id);
    if (!kudos) {
      return res.status(404).json({ error: "Kudos post not found" });
    }

    // Toggle reaction if user already clicked
    const existingIndex = kudos.reactions.findIndex(
      r => String(r.employeeId) === String(employeeId) && r.type === type
    );

    if (existingIndex > -1) {
      kudos.reactions.splice(existingIndex, 1);
    } else {
      kudos.reactions.push({ employeeId, type });
    }

    await kudos.save();
    res.json({ success: true, reactions: kudos.reactions });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/* ==========================================================================
   GET /kudos/birthdays-anniversaries — JSON Milestone List
   ========================================================================== */
router.get("/birthdays-anniversaries", async (req, res) => {
  try {
    const activeEmployees = await Employee.find({ status: "Active" }).select("firstName lastName department designation dob joiningDate");
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentDay = today.getDate();

    const birthdaysToday = activeEmployees.filter(emp => emp.dob && new Date(emp.dob).getMonth() === currentMonth && new Date(emp.dob).getDate() === currentDay);
    const anniversariesToday = activeEmployees.filter(emp => emp.joiningDate && new Date(emp.joiningDate).getMonth() === currentMonth && new Date(emp.joiningDate).getDate() === currentDay);

    res.json({ birthdaysToday, anniversariesToday });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
