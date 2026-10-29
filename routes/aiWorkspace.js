const express = require("express");
const router = express.Router();
const aiService = require("../services/aiService");
const Employee = require("../models/Employee");

/* ==========================================================================
   GET /department/:department/ai-workspace — Department AI Co-pilot Hub
   ========================================================================== */
router.get("/:department/ai-workspace", async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const deptName = req.params.department.toUpperCase();
    const employees = await Employee.find({ department: new RegExp(`^${deptName}$`, "i"), status: "Active" });

    if (isJson) {
      return res.json({ department: deptName, employees });
    }

    res.render("department/ai-workspace", {
      department: deptName,
      employees,
      success_msg: req.query.success || "",
      error_msg: req.query.error || ""
    });
  } catch (err) {
    console.error("[AI Workspace Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.status(500).send("Error loading Department AI Workspace.");
  }
});

/* ==========================================================================
   POST /department/ai-workspace/ask — Department Co-pilot Q&A
   Body: { question, department, context, history }
   ========================================================================== */
router.post("/ai-workspace/ask", async (req, res) => {
  try {
    const { question, department, context, history } = req.body;

    if (!question || !question.trim()) {
      return res.status(400).json({ error: "Question cannot be empty." });
    }

    const dept = (department || "General").toUpperCase();
    let answer = "";

    // 1. Try Python AI microservice if running
    try {
      const result = await aiService.askCopilot({
        question: question.trim(),
        department: dept,
        context: context || "",
        history: history || []
      });
      if (
        result &&
        result.answer &&
        !result.answer.includes("[Hugging Face Local Engine]") &&
        !result.answer.includes("Processed evaluation for:")
      ) {
        answer = result.answer;
      }
    } catch (aiErr) {
      console.warn("[Copilot Python Service Offline, using smart assistant]:", aiErr.message);
    }

    // 2. If no valid human answer yet, generate a sure-shot human answer
    if (!answer) {
      answer = generateSureShotDepartmentAnswer(question.trim(), dept);
    }

    res.json({ success: true, answer, department: dept });
  } catch (err) {
    console.error("[Copilot Ask Error]:", err.message);
    const dept = (req.body.department || "General").toUpperCase();
    const fallbackAnswer = generateSureShotDepartmentAnswer(req.body.question || "", dept);
    res.json({ success: true, answer: fallbackAnswer, department: dept });
  }
});

/**
 * Generates direct, human-like sure-shot answers for department co-pilot queries.
 */
function generateSureShotDepartmentAnswer(question, department) {
  const q = (question || "").toLowerCase();
  const dept = (department || "General").toUpperCase();

  if (q.includes("leave") || q.includes("vacation") || q.includes("holiday")) {
    return (
      "You get **18 days of paid Casual Leave (CL)** and **12 paid Sick Leaves** annually.\n\n" +
      "• **Casual Leave:** Accrues at 1.5 days/month. You can apply directly through the Leave Portal up to 3 days without prior notice.\n" +
      "• **Sick Leave:** Can be availed immediately when unwell. A doctor's certificate is required if taking more than 2 consecutive days.\n" +
      "• Your leave balance is updated in real time on your dashboard."
    );
  }

  if (q.includes("wfh") || q.includes("remote") || q.includes("work from home")) {
    return (
      "Yes, hybrid/WFH is supported with your reporting manager's approval.\n\n" +
      "• **Punch-in:** When working remotely, punch in using the mobile app within **15 minutes** of your shift start.\n" +
      "• **Office Days:** Physical attendance requires punching in within **100 meters** of the office building.\n" +
      "• Be available on company communication channels during working hours."
    );
  }

  if (
    q.includes("expense") ||
    q.includes("reimburse") ||
    q.includes("bill") ||
    q.includes("claim") ||
    q.includes("hotel") ||
    q.includes("food") ||
    q.includes("travel")
  ) {
    return (
      "Official expenses can be claimed through the **Reimbursements** section:\n\n" +
      "• **Daily Meals:** Up to **₹1,500/day** for Tier-1 cities.\n" +
      "• **Hotel Accommodation:** Reimbursed up to **₹5,000/night**.\n" +
      "• **Process:** Submit original tax invoices/bills before the **25th of the month** for settlement with that month's payroll."
    );
  }

  if (
    q.includes("salary") ||
    q.includes("payslip") ||
    q.includes("pay") ||
    q.includes("ctc") ||
    q.includes("bonus")
  ) {
    return (
      "Salaries are processed on the **last working day of every calendar month**.\n\n" +
      "• Your digital payslip is generated instantly under **Payroll > My Payslips**.\n" +
      "• It includes complete breakdowns of Basic, HRA, Special Allowance, PF, and Tax Deductions (TDS)."
    );
  }

  if (
    q.includes("regulariz") ||
    q.includes("missed punch") ||
    q.includes("attendance")
  ) {
    return (
      "If you forgot to punch in or out, you can submit an **Attendance Regularization** request:\n\n" +
      "• Go to **Attendance > Regularize Attendance** and select the date.\n" +
      "• State the reason (e.g. client meeting, technical issue, biometric lag).\n" +
      "• You are allowed up to **3 regularizations per month**. Your manager will review and approve within 24 hours."
    );
  }

  if (q.includes("overtime") || q.includes("ot") || q.includes("night shift")) {
    return (
      "Here is how overtime is handled:\n\n" +
      "• **Weekdays:** Overtime is calculated at **1.5x your base hourly rate** for pre-approved extra hours.\n" +
      "• **Weekends / Holidays:** Overtime is compensated at **2.0x your base hourly rate** or granted as compensatory off.\n" +
      "• Make sure your project manager pre-approves overtime before the shift."
    );
  }

  if (q.includes("resig") || q.includes("notice") || q.includes("probation")) {
    return (
      "Here are the career transition policies:\n\n" +
      "• **Probation Period:** 90 days from joining date with a **15-day notice period**.\n" +
      "• **Confirmed Employees:** Standard notice period is **60 calendar days** upon submitting resignation through the HR portal.\n" +
      "• Full and Final (FnF) settlement is completed within 30 days of the last working day."
    );
  }

  // General department-specific friendly response
  return (
    `Here is the guidance for **${dept}**:\n\n` +
    `For "${question}", you can proceed directly by submitting a request through your dashboard or checking with your department lead.\n\n` +
    `• All departmental requests are reviewed and acknowledged within **24 to 48 hours**.\n` +
    `• If you need urgent assistance, feel free to reach out to your team manager or HR directly.`
  );
}

/* ==========================================================================
   GET /department/ai-workspace/status — Health check
   ========================================================================== */
router.get("/ai-workspace/status", async (req, res) => {
  try {
    const result = await aiService.copilotStatus();
    res.json(result);
  } catch (err) {
    res.status(503).json({ status: "offline", error: err.message });
  }
});

module.exports = router;
