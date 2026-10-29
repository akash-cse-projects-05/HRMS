const express = require("express");
const router = express.Router();
const Employee = require("../models/Employee");
const SalaryRevision = require("../models/SalaryRevision");
const salaryEngine = require("../services/salaryEngine");
const aiService = require("../services/aiService");

// Middleware to check HR Authorization
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

/* ==========================================================================
   GET /hr/compensation — Company Salary Revision Dashboard
   ========================================================================== */
router.get("/hr/compensation", hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const employees = await Employee.find({ status: "Active" }).sort({ firstName: 1 });
    const revisions = await SalaryRevision.find()
      .populate("employeeId", "firstName lastName employeeCode department designation salary")
      .populate("approvedBy", "firstName lastName")
      .sort({ createdAt: -1 });

    if (isJson) {
      return res.json({ employees, revisions });
    }

    res.render("hr/compensation-dashboard", {
      employees,
      revisions,
      success_msg: req.query.success || "",
      error_msg: req.query.error || ""
    });
  } catch (err) {
    console.error("[Compensation Dashboard Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.status(500).send("Error loading compensation dashboard.");
  }
});

/* ==========================================================================
   POST /hr/compensation/simulate — Real-Time CTC Breakdown Calculator
   ========================================================================== */
router.post("/hr/compensation/simulate", async (req, res) => {
  try {
    const { annualCTC, basicPercentage, hraPercentage } = req.body;
    const ctcVal = Number(annualCTC) || 600000;

    // Call Python AI simulator with fallback to Node.js salaryEngine
    let breakdown;
    try {
      const aiSim = await aiService.simulateCTC({
        annual_ctc: ctcVal,
        basic_percentage: Number(basicPercentage) || 50,
        hra_percentage_of_basic: Number(hraPercentage) || 50
      });
      breakdown = {
        annualCTC: aiSim.annual_ctc,
        monthlyCTC: aiSim.monthly_ctc,
        monthly: aiSim.monthly_breakdown,
        annual: aiSim.annual_breakdown,
        rating: aiSim.tax_efficiency_rating
      };
    } catch (aiErr) {
      breakdown = salaryEngine.calculateCTCBreakdown(ctcVal, Number(basicPercentage) || 50, Number(hraPercentage) || 50);
    }

    res.json({ success: true, breakdown });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/* ==========================================================================
   POST /hr/compensation/propose — Propose Salary Hike / Promotion
   ========================================================================== */
router.post("/hr/compensation/propose", hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const {
      employeeId,
      effectiveDate,
      revisionType,
      newDesignation,
      targetCTC,
      hikePercentage,
      reason
    } = req.body;

    const employee = await Employee.findById(employeeId);
    if (!employee) {
      if (isJson) return res.status(404).json({ error: "Employee not found" });
      return res.redirect("/hr/compensation?error=Employee+not+found");
    }

    const currentMonthlySalary = Number(employee.salary) || 30000;
    const currentAnnualCTC = currentMonthlySalary * 12;

    let finalAnnualCTC = Number(targetCTC);
    let finalHikePercent = Number(hikePercentage);

    if (finalHikePercent && !finalAnnualCTC) {
      finalAnnualCTC = Math.round(currentAnnualCTC * (1 + finalHikePercent / 100));
    } else if (finalAnnualCTC && !finalHikePercent) {
      finalHikePercent = Math.round(((finalAnnualCTC - currentAnnualCTC) / currentAnnualCTC) * 100 * 10) / 10;
    }

    const calc = salaryEngine.calculateCTCBreakdown(finalAnnualCTC);

    const revision = new SalaryRevision({
      employeeId: employee._id,
      effectiveDate: new Date(effectiveDate || Date.now()),
      revisionType: revisionType || "Annual Increment",
      previousDesignation: employee.designation,
      newDesignation: newDesignation || employee.designation,
      previousSalary: currentMonthlySalary,
      newSalary: calc.monthly.grossSalary,
      hikePercentage: finalHikePercent || 0,
      breakdown: {
        basicSalary: calc.monthly.basicSalary,
        hra: calc.monthly.hra,
        specialAllowance: calc.monthly.specialAllowance,
        pf: calc.monthly.employeePf,
        gratuity: calc.annual.gratuity / 12,
        professionalTax: calc.monthly.professionalTax,
        netPay: calc.monthly.netPay
      },
      reason: reason || "Annual Appraisal Performance Review",
      status: "PROPOSED",
      proposedBy: req.session.employeeId || null
    });
    await revision.save();

    if (isJson) {
      return res.json({ success: true, message: "Salary revision proposed successfully!", revision });
    }

    res.redirect("/hr/compensation?success=Salary+revision+proposed+successfully!");
  } catch (err) {
    console.error("[Propose Revision Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.redirect(`/hr/compensation?error=${encodeURIComponent(err.message)}`);
  }
});

/* ==========================================================================
   POST /hr/compensation/:id/approve — Approve Hike & Update Employee Record
   ========================================================================== */
router.post("/hr/compensation/:id/approve", hrAuth, async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json") || req.body.format === "json";

  try {
    const revision = await SalaryRevision.findById(req.params.id);
    if (!revision) {
      if (isJson) return res.status(404).json({ error: "Revision record not found" });
      return res.redirect("/hr/compensation?error=Revision+not+found");
    }

    revision.status = "APPROVED";
    revision.approvedBy = req.session.employeeId || null;
    revision.approvalDate = new Date();
    await revision.save();

    // Update master Employee salary and designation
    const employee = await Employee.findById(revision.employeeId);
    if (employee) {
      employee.salary = revision.newSalary;
      if (revision.newDesignation && revision.newDesignation !== employee.designation) {
        employee.designation = revision.newDesignation;
      }
      await employee.save();
    }

    if (isJson) {
      return res.json({ success: true, message: "Revision approved and employee master record updated!", revision });
    }

    res.redirect("/hr/compensation?success=Compensation+revision+approved+and+applied!");
  } catch (err) {
    console.error("[Approve Revision Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.redirect(`/hr/compensation?error=${encodeURIComponent(err.message)}`);
  }
});

/* ==========================================================================
   GET /hr/compensation/:id/letter — Branded Increment / Promotion Letter
   ========================================================================== */
router.get("/hr/compensation/:id/letter", async (req, res) => {
  try {
    const revision = await SalaryRevision.findById(req.params.id)
      .populate("employeeId")
      .populate("approvedBy", "firstName lastName designation");

    if (!revision) {
      return res.status(404).send("Compensation Revision letter not found.");
    }

    revision.letterGenerated = true;
    await revision.save();

    res.render("hr/increment-letter", {
      revision,
      employee: revision.employeeId,
      company: {
        name: "RSR AVIATION SERVICES PVT LTD",
        address: "Airport Road, Terminal 2 Executive Center, New Delhi - 110037",
        cin: "U62200DL2024PTC394851",
        website: "www.rsraviation.com",
        hrEmail: "hr@rsraviation.com"
      }
    });
  } catch (err) {
    console.error("[Letter Generation Error]:", err);
    res.status(500).send("Error generating increment letter.");
  }
});

/* ==========================================================================
   GET /employee/:id/compensation-history — Career Growth Timeline View
   ========================================================================== */
router.get("/employee/:id/compensation-history", async (req, res) => {
  const isJson = req.query.format === "json" || req.headers.accept?.includes("application/json");

  try {
    const employee = await Employee.findById(req.params.id);
    if (!employee) {
      if (isJson) return res.status(404).json({ error: "Employee not found" });
      return res.status(404).send("Employee not found.");
    }

    const history = await SalaryRevision.find({ employeeId: employee._id })
      .populate("approvedBy", "firstName lastName")
      .sort({ effectiveDate: -1 });

    if (isJson) {
      return res.json({ employee, history });
    }

    res.render("employee/compensation-history", {
      employee,
      history
    });
  } catch (err) {
    console.error("[Compensation History Error]:", err);
    if (isJson) return res.status(500).json({ error: err.message });
    res.status(500).send("Error loading compensation history.");
  }
});

module.exports = router;
