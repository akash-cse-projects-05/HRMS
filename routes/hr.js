const express = require("express");
const router = express.Router();
const mongoose = require("mongoose");

const Employee = require("../models/Employee");
const Attendance = require("../models/Attendence"); // keep spelling same as file
const Leave = require("../models/Leave");
const User = require('../models/User');

const Document = require('../models/Documents');
const CompanySettings = require('../models/CompanySettings');
const Tenant = require('../models/master/Tenant');
const multer = require('multer');

// Configure Multer for Logo Upload
const logoUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 2 * 1024 * 1024 }, // 2MB max
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files (PNG, JPG, JPEG, SVG) are allowed for company logo.'));
    }
  }
});
/* ==========================
   HR AUTH MIDDLEWARE
========================== */
function hrAuth(req, res, next) {
  if (!req.session.userId || req.session.role !== "HR") {
    const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json');
    if (isJson) {
      return res.status(401).json({ error: "Unauthorized. HR session required." });
    }
    return res.redirect("/hr/hr-login");
  }
  next();
}

/* ==========================
   HR LOGIN
========================== */

// GET HR Login Page
router.get("/hr-login", (req, res) => {
  if (req.session.userId && req.session.role === "HR") {
    return res.redirect("/hr/dashboard");
  }
  res.render("hr/login", {
    company: req.query.company || "",
    error: req.query.error || ""
  });
});

const rateLimit = require("express-rate-limit");
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  message: "Too many login attempts, please try again after 15 minutes.",
  standardHeaders: true,
  legacyHeaders: false,
});

// POST HR Login
router.post("/hr-login", authLimiter, async (req, res) => {
  const isJson = req.xhr || 
                 req.query.format === 'json' || 
                 req.body?.format === 'json' || 
                 req.headers['content-type']?.includes('application/json') ||
                 req.headers.accept?.includes('application/json');

  const rawTenantId = req.body.tenantId || req.headers['x-tenant-id'] || req.query.tenantId || req.session?.tenantId || "rsr";
  const lowercaseTenantId = rawTenantId ? rawTenantId.toLowerCase().trim() : "rsr";
  const username = (req.body.username || req.body.employeeCode || req.body.email || "").trim();
  const password = req.body.password || "";

  try {


    if (!lowercaseTenantId) {
      if (isJson) {
        return res.status(400).json({ error: "Please enter your Company ID" });
      }
      return res.render("hr/login", { error: "Please enter your Company ID", company: "" });
    }

    req.session.tenantId = lowercaseTenantId;

    const { getTenantConnection } = require("../utils/tenantManager");
    let tenantConn;
    try {
      tenantConn = await getTenantConnection(lowercaseTenantId);
    } catch (dbErr) {
      req.session.tenantId = undefined;
      const isConnectionError = dbErr.name === 'MongoNetworkError' || 
                                dbErr.name === 'MongooseError' ||
                                dbErr.message.includes('connect') || 
                                dbErr.message.includes('buffering timed out') ||
                                mongoose.connection.readyState === 0 ||
                                mongoose.connection.readyState === 3;

      const errorMsg = isConnectionError 
        ? "Could not connect to cloud database, check your internet connection."
        : `Company ID '${rawTenantId}' not found or inactive.`;

      if (isJson) {
        return res.status(isConnectionError ? 503 : 404).json({ error: errorMsg });
      }
      return res.render("hr/login", { error: errorMsg, company: rawTenantId });
    }

    const UserModel = tenantConn.model("User", User.schema);
    const EmployeeModel = tenantConn.model("Employee", Employee.schema);

    console.log(`[HR/Login] Attempting HR login: tenant='${lowercaseTenantId}', username='${username}'`);

    const cleanEscape = username.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // 1. Find User by username / employeeCode (case-insensitive)
    let user = await UserModel.findOne({
      username: { $regex: new RegExp(`^${cleanEscape}$`, 'i') }
    });

    // 2. Fallback: Find user by Employee email address
    if (!user) {
      const matchedEmp = await EmployeeModel.findOne({
        email: { $regex: new RegExp(`^${cleanEscape}$`, 'i') }
      });
      if (matchedEmp) {
        user = await UserModel.findOne({ employeeId: matchedEmp._id });
      }
    }

    if (!user) {
      console.log(`[HR/Login] HR user not found for username/email '${username}' in tenant '${lowercaseTenantId}'`);
      if (isJson) {
        return res.status(401).json({ error: "Invalid credentials: user not found" });
      }
      return res.render("hr/login", { error: "Invalid credentials", company: rawTenantId });
    }

    // 2. Verify password
    const isMatch = await user.comparePassword(password);

    if (!isMatch) {
      if (isJson) {
        return res.status(401).json({ error: "Invalid credentials" });
      }
      return res.render("hr/login", { error: "Invalid credentials", company: rawTenantId });
    }

    // 3. Find associated Employee to check Role/Department
    const employee = await EmployeeModel.findOne({
      _id: user.employeeId,
      status: "Active"
    });

    if (!employee) {
      if (isJson) {
        return res.status(401).json({ error: "Employee record not found or inactive" });
      }
      return res.render("hr/login", { error: "Employee record not found or inactive", company: rawTenantId });
    }

    // 4. Role validation
    if (employee.department !== "HR" && user.role !== "HR") {
      if (isJson) {
        return res.status(403).json({ error: "Access denied: Not an HR" });
      }
      return res.render("hr/login", { error: "Access denied: Not an HR", company: rawTenantId });
    }

    // 5. Create HR session
    req.session.userId = user._id; // Store User ID in session
    req.session.employeeId = employee._id;
    req.session.role = "HR";
    req.session.tenantId = lowercaseTenantId;

    console.log("✅ HR logged in:", employee.employeeCode);

    if (isJson) {
      const cookieSignature = require('cookie-signature');
      const signedSid = 's:' + cookieSignature.sign(req.sessionID, process.env.SESSION_SECRET || "rsr_hrms_secret");
      return req.session.save((err) => {
        if (err) console.error("Session save error:", err);
        return res.json({ success: true, role: 'HR', employeeName: employee.firstName, employeeId: employee._id, tenantId: lowercaseTenantId, sessionId: signedSid });
      });
    }
    res.redirect("/hr/dashboard");

  } catch (err) {
    require('fs').appendFileSync('error.log', err.stack + '\n');
    console.error(err);
    const isConnectionError = err.name === 'MongoNetworkError' || 
                              err.name === 'MongooseError' ||
                              err.message.includes('connect') || 
                              err.message.includes('buffering timed out') ||
                              mongoose.connection.readyState === 0 ||
                              mongoose.connection.readyState === 3;

    const errorMsg = isConnectionError 
      ? "Could not connect to cloud database, check your internet connection."
      : "Database connection failed: " + err.message;

    if (req.headers.accept?.includes('application/json')) {
      return res.status(isConnectionError ? 503 : 500).json({ error: errorMsg });
    }
    res.render("hr/login", { error: errorMsg, company: req.body.tenantId || "" });
  }
});

/* ==========================
   HR DASHBOARD
========================== */
router.get("/dashboard", hrAuth, async (req, res) => {
  try {
    const today = new Date().toISOString().slice(0, 10);

    const totalEmployees = await Employee.countDocuments({ status: "Active" });

    const todayAttendance = await Attendance.find({ date: today })
      .populate("employeeId")
      .populate("shiftId")
      .sort({ punchIn: -1 });

    const present = todayAttendance.length;
    const completed = todayAttendance.filter(a => a.punchOut).length;
    const inProgress = todayAttendance.filter(a => !a.punchOut).length;
    const absent = Math.max(totalEmployees - present, 0);

    // List of active employees who have NOT punched in today
    const punchedEmployeeIds = todayAttendance.map(a => a.employeeId?._id?.toString()).filter(Boolean);
    const absentEmployees = await Employee.find({
      status: "Active",
      _id: { $nin: punchedEmployeeIds }
    }).select("firstName lastName employeeCode department designation profilePic email").sort({ firstName: 1 });

    const Project = require("../models/Project");
    const Appraisal = require("../models/Appraisal");

    let projectQuery = { status: "Active" };
    if (req.session.role !== "HR" && req.session.employeeId) {
      const manager = await Employee.findById(req.session.employeeId);
      if (manager) {
        projectQuery = { status: "Active", departments: manager.department };
      }
    }

    const projects = await Project.find(projectQuery).sort({ createdAt: -1 });
    const appraisals = await Appraisal.find().populate("employeeId").sort({ createdAt: -1 });
    const pendingResignations = await Employee.find({ resignationStatus: "Pending" });

    const Announcement = require("../models/Announcement");
    const Notification = require("../models/Notification");
    const fifteenDaysAgo = new Date(Date.now() - 15 * 24 * 60 * 60 * 1000);
    const latestAnnouncements = await Announcement.find({ date: { $gte: fifteenDaysAgo } }).sort({ date: -1 }).limit(5);
    const latestNotifications = await Notification.find({ date: { $gte: fifteenDaysAgo } }).sort({ date: -1 }).limit(5);

    if (req.query.format === 'json' || req.headers.accept?.includes('application/json')) {
      return res.json({
        totalEmployees,
        present,
        completed,
        inProgress,
        absent,
        todayAttendance,
        absentEmployees,
        projects,
        appraisals,
        pendingResignations,
        latestAnnouncements,
        latestNotifications
      });
    }

    res.render("hr/dashboard", {
      totalEmployees,
      present,
      completed,
      inProgress,
      absent,
      todayAttendance,
      absentEmployees,
      projects,
      appraisals,
      pendingResignations,
      latestAnnouncements,
      latestNotifications
    });

  } catch (err) {
    console.error(err);
    if (req.headers.accept?.includes('application/json')) {
      return res.status(500).json({ error: "Failed to load HR dashboard" });
    }
    res.render("hr/login", { error: "Failed to load HR dashboard. Database connection might be unstable." });
  }
});

/* ==========================
   HR LIVE ATTENDANCE TRACKING CONSOLE
========================== */
router.get("/live-attendance", hrAuth, async (req, res) => {
  try {
    const today = new Date().toISOString().slice(0, 10);
    const totalEmployees = await Employee.countDocuments({ status: "Active" });

    const todayAttendance = await Attendance.find({ date: today })
      .populate("employeeId")
      .populate("shiftId")
      .sort({ punchIn: -1 });

    const present = todayAttendance.length;
    const completed = todayAttendance.filter(a => a.punchOut).length;
    const inProgress = todayAttendance.filter(a => !a.punchOut).length;
    const absent = Math.max(totalEmployees - present, 0);

    const punchedEmployeeIds = todayAttendance.map(a => a.employeeId?._id?.toString()).filter(Boolean);
    const absentEmployees = await Employee.find({
      status: "Active",
      _id: { $nin: punchedEmployeeIds }
    }).select("firstName lastName employeeCode department designation profilePic email").sort({ firstName: 1 });

    const CompanySettings = require("../models/CompanySettings");
    const companySettings = await CompanySettings.findOne();

    if (req.query.format === 'json' || req.headers.accept?.includes('application/json')) {
      return res.json({
        date: today,
        totalEmployees,
        present,
        completed,
        inProgress,
        absent,
        todayAttendance,
        absentEmployees,
        companySettings
      });
    }

    res.render("hr/live-attendance", {
      date: today,
      totalEmployees,
      present,
      completed,
      inProgress,
      absent,
      todayAttendance,
      absentEmployees,
      companySettings
    });
  } catch (err) {
    console.error("Live attendance error:", err);
    res.status(500).send("Error loading live attendance tracking console.");
  }
});

/* ==========================
   ATTENDANCE HISTORY
========================== */


/* ==========================
   HR LEAVE MANAGEMENT
========================== */

// View all leave requests (Pending stay active; Approved/Rejected stay for 15 days)
router.get("/leaves", hrAuth, async (req, res) => {
  try {
    const fifteenDaysAgo = new Date(Date.now() - 15 * 24 * 60 * 60 * 1000);

    const leaves = await Leave.find({
      $or: [
        { status: "PENDING" },
        {
          status: { $in: ["APPROVED", "REJECTED"] },
          $or: [
            { actionAt: { $gte: fifteenDaysAgo } },
            { appliedAt: { $gte: fifteenDaysAgo } }
          ]
        }
      ]
    })
      .populate("employeeId")
      .sort({ appliedAt: -1 });

    if (req.query.format === 'json' || req.headers.accept?.includes('application/json')) {
      return res.json({ leaves });
    }

    res.render("hr/leaves", { leaves });

  } catch (err) {
    console.error(err);
    if (req.headers.accept?.includes('application/json')) {
      return res.status(500).json({ error: "Leave dashboard error" });
    }
    res.status(500).send("Leave dashboard error");
  }
});

// Approve / Reject leave
// router.post("/leave-action/:id", hrAuth, async (req, res) => {
//   try {
//     const { status, hrRemark } = req.body;

//     await Leave.findByIdAndUpdate(req.params.id, {
//       status,
//       hrRemark
//     });

//     res.redirect("/hr/leaves");

//   } catch (err) {
//     console.error(err);
//     res.redirect('/hr/dashboard?error=leave_action_error');
//   }
// });
router.post("/leave-action/:id", hrAuth, async (req, res) => {
  try {
    let { status, hrRemark } = req.body;
    if (status) status = status.toUpperCase();
    const leave = await Leave.findById(req.params.id);

    if (!leave) {
      return res.redirect('/hr/dashboard?error=leave_not_found');
    }

    // Prevent status change if already approved or rejected
    if (leave.status === "APPROVED" || leave.status === "REJECTED") {
      return res.redirect('/hr/dashboard?error=already_finalized');
    }

    const employee = await Employee.findById(leave.employeeId);
    if (!employee) {
      return res.redirect('/hr/dashboard?error=employee_not_found');
    }

    // Handle APPROVED status
    if (status === "APPROVED") {
      if (leave.leaveType === "LOP") {
        // Track LOP count
        const newLopCount = (employee.lopCount || 0) + leave.totalDays;
        const newLopDaysThisMonth = (employee.lopDaysThisMonth || 0) + leave.totalDays;

        await Employee.updateOne(
          { _id: employee._id },
          {
            $set: {
              lopCount: newLopCount,
              lopDaysThisMonth: newLopDaysThisMonth
            }
          }
        );

        // Calculate and apply LOP deduction to payslip
        const Payslip = require('../models/Payslip');
        const fromDate = new Date(leave.fromDate);
        const month = fromDate.getMonth() + 1;
        const year = fromDate.getFullYear();

        const payslip = await Payslip.findOne({
          employee: employee._id,
          month,
          year
        });

        if (payslip) {
          const perDaySalary = payslip.basicSalary / 30;
          const lopDeduction = perDaySalary * leave.totalDays;

          // Add to deduction details
          payslip.deductionDetails.push({
            type: 'LOP',
            label: `Loss of Pay for ${leave.totalDays} day(s)`,
            amount: lopDeduction
          });

          // Update LOP days count
          payslip.lopDays += leave.totalDays;

          payslip.deductions += lopDeduction;
          payslip.netPay = (payslip.basicSalary || 0) + (payslip.allowances || 0) + (payslip.bonuses || 0) + (payslip.reimbursements || 0) - (payslip.deductions || 0) - (payslip.pf || 0) - (payslip.professionalTax || 0) - (payslip.taxes || 0);
          await payslip.save();

          console.log(`✅ LOP deduction applied: ₹${lopDeduction.toFixed(2)} for ${leave.totalDays} days`);
        }
      } else {
        // Regular leave - deduct from leave balance
        if (employee.leaveBalance < leave.totalDays) {
          return res.redirect('/hr/dashboard?error=insufficient_balance');
        }
        const newBalance = employee.leaveBalance - leave.totalDays;
        await Employee.updateOne(
          { _id: employee._id },
          { $set: { leaveBalance: newBalance } }
        );
      }
    }

    // Update leave status, HR remark, and timestamp
    leave.status = status;
    leave.hrRemark = hrRemark;
    leave.actionAt = new Date();
    leave.actionBy = req.session.username || req.session.employeeId || 'HR';
    if (status === "REJECTED") {
      leave.rejectionReason = req.body.rejectionReason || hrRemark;
    }
    // Ensure department is set
    if (!leave.department) {
      if (employee && employee.department) {
        leave.department = employee.department;
      }
    }
    await leave.save();

    // --- SEND EMAIL NOTIFICATION (Approved/Rejected) ---
    try {
      if (employee.email) {
        const { sendEmail } = require('../utils/email');

        let emailSubject, messageHeader, statusColor;

        if (status === "APPROVED") {
          emailSubject = 'Leave Approved - RSR Aviation (HR)';
          messageHeader = 'Leave Approved';
          statusColor = '#28a745';
        } else {
          emailSubject = 'Leave Rejected - RSR Aviation (HR)';
          messageHeader = 'Leave Rejected';
          statusColor = '#dc3545';
        }

        await sendEmail({
          to: employee.email,
          subject: emailSubject,
          html: `
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
              <h2 style="color: ${statusColor};">${messageHeader}</h2>
              <p>Dear <strong>${employee.firstName}</strong>,</p>
              <p>Your leave request has been <strong>${status}</strong> by HR.</p>
              ${status === 'REJECTED' ? `<p style="color: #d9534f;"><strong>HR Remark/Reason:</strong> ${leave.hrRemark || leave.rejectionReason}</p>` : ''}
              <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Leave Type:</strong></td><td style="padding: 10px; border-bottom: 1px solid #eee;">${leave.leaveType}</td></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>From Date:</strong></td><td style="padding: 10px; border-bottom: 1px solid #eee;">${leave.fromDate}</td></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>To Date:</strong></td><td style="padding: 10px; border-bottom: 1px solid #eee;">${leave.toDate}</td></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Total Days:</strong></td><td style="padding: 10px; border-bottom: 1px solid #eee;">${leave.totalDays}</td></tr>
              </table>
              <p style="color: #888; font-size: 12px; margin-top: 20px;">RSR Aviation HRMS</p>
            </div>
          `
        });
        console.log(`HR Email sent to ${employee.email} [Status: ${status}]`);
      }
    } catch (emailErr) {
      console.error("HR Email error:", emailErr);
    }

    if (req.headers.accept?.includes('application/json')) {
      return res.json({ success: true, leave });
    }
    res.redirect("/hr/leaves");

  } catch (err) {
    console.error(err);
    if (req.headers.accept?.includes('application/json')) {
      return res.status(500).json({ error: "Leave action error" });
    }
    res.redirect('/hr/dashboard?error=leave_action_error');
  }
});
/* ==========================
   LOP STATISTICS
========================== */
router.get("/lop-stats", hrAuth, async (req, res) => {
  try {
    const employees = await Employee.find({ status: "Active" })
      .select("employeeCode firstName lastName department lopCount lopDaysThisMonth")
      .sort({ lopCount: -1 });

    const totalLopDays = employees.reduce((sum, emp) => sum + emp.lopCount, 0);
    const employeesWithLop = employees.filter(emp => emp.lopCount > 0).length;

    res.json({
      success: true,
      totalLopDays,
      employeesWithLop,
      employees
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: err.message });
  }
});

/* ==========================
   RESET MONTHLY LOP COUNTER
========================== */
router.post("/reset-monthly-lop", hrAuth, async (req, res) => {
  try {
    await Employee.updateMany(
      {},
      { $set: { lopDaysThisMonth: 0 } }
    );

    res.json({
      success: true,
      message: "Monthly LOP counters reset for all employees"
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: err.message });
  }
});

/* ==========================
   HR LOGOUT
========================== */
// HR LOGOUT
router.get("/logout", hrAuth, (req, res) => {
  req.session.destroy((err) => {
    if (err) console.error("Session destroy error:", err);
    res.clearCookie("connect.sid");
    res.redirect("/hr/hr-login");
  });
});



// TO GET THE OVERALL ATTENDANCE OF THE EMPLOYEES

// Example: routes/hr.js
router.get("/attendance-history", hrAuth, async (req, res) => {
  try {
    const query = { status: "Active" };
    if (req.query.search) {
      const searchRegex = new RegExp(req.query.search, 'i');
      query.$or = [
        { firstName: searchRegex },
        { lastName: searchRegex },
        { employeeCode: searchRegex }
      ];
    }
    const employees = await Employee.find(query);

    const attendanceStats = await Promise.all(
      employees.map(async emp => {
        const presentDays = await Attendance.countDocuments({
          employeeId: emp._id,
          punchOut: { $ne: null }
        });

        return {
          employeeCode: emp.employeeCode,
          name: emp.firstName + " " + (emp.lastName || ""),
          presentDays
        };
      })
    );

    //  VERY IMPORTANT
    // console.log("attendanceStats sent to EJS:", attendanceStats);

    res.render("hr/history", {
      attendanceStats,
      searchQuery: req.query.search
    });

  } catch (err) {
    console.error(err);
    res.status(500).send("Attendance summary error");
  }
});



//hr report 

// List all users
router.get('/users', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json');
  console.log(`[Backend] GET /hr/users called. isJson: ${isJson}, query:`, req.query);
  try {
    const users = await User.find().populate('employeeId');
    console.log(`[Backend] GET /hr/users - Found ${users.length} users in DB.`);
    if (isJson) {
      return res.json({ success: true, users });
    }
    res.render('hr/users', { users });
  } catch (err) {
    console.error(err);
    if (isJson) return res.status(500).json({ error: "Failed to load user list" });
    res.status(500).send("Error fetching users");
  }
});

// HR views a user's profile
router.get('/profile/:userId', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json');
  try {
    const user = await User.findById(req.params.userId).populate('employeeId');
    if (!user) {
      if (isJson) return res.status(404).json({ error: "User not found" });
      return res.status(404).send('User not found');
    }
    const documents = await Document.find({ user: req.params.userId, name: { $ne: '__OVERALL_STATUS__' } });
    const statusDoc = await Document.findOne({ name: '__OVERALL_STATUS__' });
    if (isJson) {
      return res.json({
        success: true,
        user,
        employee: user.employeeId,
        documents,
        status: statusDoc?.overallStatus || 'OPEN'
      });
    }
    res.render('hr/profile', {
      user,
      employee: user.employeeId,
      documents,
      status: statusDoc?.overallStatus || 'OPEN'
    });
  } catch (err) {
    console.error(err);
    if (isJson) return res.status(500).json({ error: "Failed to load user profile" });
    res.status(500).send("Error loading profile");
  }
});


// HR updates overall status
router.post('/profile/:userId/status', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';
  try {
    let statusDoc = await Document.findOne({ name: '__OVERALL_STATUS__' });
    if (!statusDoc) statusDoc = new Document({ name: '__OVERALL_STATUS__' });
    statusDoc.overallStatus = req.body.status;
    await statusDoc.save();
    if (isJson) {
      return res.json({ success: true, status: statusDoc.overallStatus });
    }
    res.redirect(`/hr/profile/${req.params.userId}`);
  } catch (err) {
    console.error(err);
    if (isJson) return res.status(500).json({ error: "Failed to update status" });
    res.redirect(`/hr/profile/${req.params.userId}?error=status_update_failed`);
  }
});

// HR approves/rejects a document
router.post('/profile/:userId/document/:docId/:action', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';
  try {
    const status = req.params.action === 'approve' ? 'APPROVED' : 'REJECTED';
    const doc = await Document.findByIdAndUpdate(req.params.docId, { status }, { new: true });
    if (isJson) {
      return res.json({ success: true, document: doc });
    }
    res.redirect(`/hr/profile/${req.params.userId}`);
  } catch (err) {
    console.error(err);
    if (isJson) return res.status(500).json({ error: "Failed to update document status" });
    res.redirect(`/hr/profile/${req.params.userId}?error=document_update_failed`);
  }
});



// HR changes THEIR OWN password
router.post('/change-my-password', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';
  try {
    const { newPassword, confirmPassword } = req.body;

    if (newPassword !== confirmPassword) {
      if (isJson) return res.status(400).json({ error: "New passwords do not match" });
      return res.redirect('back');
    }
    if (!newPassword || newPassword.length < 6) {
      if (isJson) return res.status(400).json({ error: "Password must be at least 6 characters" });
      return res.redirect('back');
    }

    const user = await User.findById(req.session.userId); // Change OWN password
    if (!user) {
      if (isJson) return res.status(404).json({ error: "User not found" });
      return res.status(404).send('User not found');
    }

    user.password = newPassword;
    await user.save();

    if (isJson) return res.json({ success: true, message: "Password updated successfully" });
    res.redirect('/hr/dashboard?passwordUpdated=true');
  } catch (err) {
    console.error(err);
    if (isJson) return res.status(500).json({ error: "Error updating password" });
    res.status(500).send("Error updating password");
  }
});

// HR toggles employee status (Active/Inactive)
router.post('/toggle-status/:employeeId', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';
  try {
    const employee = await Employee.findById(req.params.employeeId);
    if (!employee) {
      if (isJson) return res.status(404).json({ error: 'Employee not found' });
      return res.status(404).send('Employee not found');
    }

    // Prevent HR from deactivating themselves
    if (employee._id.toString() === req.session.employeeId.toString()) {
      if (isJson) return res.status(400).json({ error: 'Cannot deactivate yourself' });
      return res.redirect('/hr/users?error=cannot_deactivate_self');
    }

    employee.status = (employee.status === 'Active') ? 'Inactive' : 'Active';
    await employee.save();

    console.log(`User ${employee.employeeCode} status changed to ${employee.status} by HR`);
    if (isJson) {
      return res.json({ success: true, status: employee.status });
    }
    res.redirect('/hr/users');
  } catch (err) {
    console.error(err);
    if (isJson) return res.status(500).json({ error: "Error updating status" });
    res.status(500).send("Error updating status");
  }
});

// HR permanently deletes employee (Only if Inactive or Resigned)
router.post('/delete-employee/:employeeId', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';
  try {
    const employee = await Employee.findById(req.params.employeeId);
    if (!employee) {
      if (isJson) return res.status(404).json({ error: 'Employee not found' });
      return res.redirect('/hr/users?error=employee_not_found');
    }

    // Prevent HR from deleting their own account
    if (employee._id.toString() === req.session.employeeId?.toString()) {
      if (isJson) return res.status(400).json({ error: 'Cannot delete your own account' });
      return res.redirect('/hr/users?error=cannot_delete_self');
    }

    // Enforce condition: Must be Inactive or Resigned
    if (employee.status !== 'Inactive' && employee.status !== 'Resigned') {
      const errorMsg = 'Active employees cannot be permanently deleted. Please deactivate or terminate the employee first.';
      if (isJson) return res.status(400).json({ error: errorMsg });
      return res.redirect('/hr/users?error=' + encodeURIComponent(errorMsg));
    }

    const employeeId = employee._id;
    const employeeName = `${employee.firstName} ${employee.lastName}`;

    // Clean up all related tenant records
    const Attendance = require("../models/Attendence");
    const Leave = require("../models/Leave");
    const Payslip = require("../models/Payslip");
    const Document = require("../models/Documents");
    const EmployeeChecklist = require("../models/EmployeeChecklist");
    const Task = require("../models/Task");
    const Timesheet = require("../models/Timesheet");
    const Expense = require("../models/Expense");
    const Trip = require("../models/Trip");
    const Regularization = require("../models/Regularization");

    // 1. Delete associated user login account(s)
    const users = await User.find({ employeeId });
    const userIds = users.map(u => u._id);
    await User.deleteMany({ employeeId });

    // 2. Delete employee documents
    if (userIds.length > 0) {
      await Document.deleteMany({ user: { $in: userIds } });
    }

    // 3. Delete attendance, leaves, payslips, checklists, tasks, timesheets, expenses
    await Attendance.deleteMany({ employeeId });
    await Leave.deleteMany({ employeeId });
    await Payslip.deleteMany({ employee: employeeId });
    await EmployeeChecklist.deleteMany({ employeeId });
    await Task.deleteMany({ assignedTo: employeeId });
    await Timesheet.deleteMany({ employeeId });
    await Expense.deleteMany({ employeeId });
    await Trip.deleteMany({ employeeId });
    await Regularization.deleteMany({ employeeId });

    // 4. Finally delete the employee record
    await Employee.findByIdAndDelete(employeeId);

    console.log(`[HR Permanent Deletion] Successfully deleted employee ${employeeName} (${employee.employeeCode}) and all linked records.`);

    if (isJson) {
      return res.json({ success: true, message: `Employee ${employeeName} permanently deleted` });
    }
    res.redirect('/hr/users?deleted=true');

  } catch (err) {
    console.error("Error permanently deleting employee:", err);
    if (isJson) return res.status(500).json({ error: "Failed to delete employee: " + err.message });
    res.redirect('/hr/users?error=' + encodeURIComponent(err.message));
  }
});

/* ==========================
   HR IN-APP BILLING PORTAL
   ========================== */

// GET: View HR Billing & Subscription Panel
router.get("/billing", hrAuth, async (req, res) => {
  try {
    const Tenant = require("../models/master/Tenant");
    let tenantId = req.session.tenantId;
    if (tenantId === "default") {
      tenantId = "rsr";
    }

    // Fetch tenant configuration from the central registry
    const tenant = await Tenant.findOne({ tenantId });
    if (!tenant) {
      return res.redirect("/hr/dashboard?error=Tenant+details+not+found.");
    }

    // Calculate days remaining
    const daysRemaining = tenant.subscriptionExpiry
      ? Math.max(0, Math.ceil((new Date(tenant.subscriptionExpiry) - new Date()) / (1000 * 60 * 60 * 24)))
      : 0;

    res.render("hr/billing", {
      tenant,
      daysRemaining,
      razorpayKeyId: process.env.RAZORPAY_KEY_ID,
      success: req.query.success || "",
      error: req.query.error || ""
    });
  } catch (err) {
    console.error("Error loading HR billing page:", err);
    res.redirect("/hr/dashboard?error=" + encodeURIComponent(err.message));
  }
});

// POST: Verify and Renew Subscription (Extend Expiry by 30 Days)
router.post("/billing/renew", hrAuth, async (req, res) => {
  const {
    razorpay_payment_id,
    razorpay_order_id,
    razorpay_signature,
    selectedPlan
  } = req.body;

  const crypto = require("crypto");
  const Tenant = require("../models/master/Tenant");

  try {
    // 1. Cryptographic Payment Verification
    if (!razorpay_payment_id || !razorpay_order_id || !razorpay_signature) {
      return res.redirect("/hr/billing?error=Missing+payment+references.+Renewal+aborted.");
    }

    const hmac = crypto.createHmac("sha256", (process.env.RAZORPAY_KEY_SECRET || "").trim());
    hmac.update(razorpay_order_id + "|" + razorpay_payment_id);
    const generatedSignature = hmac.digest("hex");

    if (generatedSignature !== razorpay_signature) {
      console.error("[Billing Renewal Signature Mismatch]");
      return res.redirect("/hr/billing?error=Payment+verification+failed.+Invalid+signature.");
    }

    // 2. Extend subscription by 30 days
    let tenantId = req.session.tenantId;
    if (tenantId === "default") {
      tenantId = "rsr";
    }
    const tenant = await Tenant.findOne({ tenantId });
    if (!tenant) {
      return res.redirect("/hr/billing?error=Tenant+record+not+found.");
    }

    // Base date: If current subscription is still active, extend from the expiry date.
    // If it has already expired, extend from the current timestamp.
    const baseDate = (tenant.subscriptionExpiry && tenant.subscriptionExpiry > new Date())
      ? new Date(tenant.subscriptionExpiry)
      : new Date();

    baseDate.setDate(baseDate.getDate() + 30); // Add 30 days

    tenant.subscriptionExpiry = baseDate;
    tenant.paymentStatus = "paid";
    tenant.subscriptionPlan = selectedPlan || tenant.subscriptionPlan;
    tenant.razorpayOrderId = razorpay_order_id;
    tenant.razorpayPaymentId = razorpay_payment_id;

    await tenant.save();

    console.log(`✅ Subscription successfully renewed for company '${tenantId}' by 30 days. Expiry: ${baseDate}`);
    res.redirect("/hr/billing?success=Subscription+successfully+renewed+for+30+days!");

  } catch (err) {
    console.error("Error processing subscription renewal:", err);
    res.redirect("/hr/billing?error=" + encodeURIComponent("Renewal error: " + err.message));
  }
});

// POST: HR Process Resignation (Approve/Reject)
router.post("/resignation/:employeeId/action", hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';
  const { action } = req.body;

  try {
    const employee = await Employee.findById(req.params.employeeId);
    if (!employee) {
      if (isJson) return res.status(404).json({ error: 'Employee not found' });
      return res.status(404).send('Employee not found');
    }

    const { sendEmail } = require('../utils/email');

    if (action === 'approve') {
      employee.resignationStatus = 'Approved';
      employee.status = 'Resigned';

      if (employee.email) {
        try {
          await sendEmail({
            to: employee.email,
            subject: 'Resignation Accepted - HRMS',
            html: `<p>Dear ${employee.firstName},</p><p>Your resignation has been accepted by the management. HR will contact you for the exit process.</p>`
          });
        } catch (emailErr) {
          console.error("Email send failed for resignation approval:", emailErr);
        }
      }

      // Automatically trigger Offboarding Checklist run if template exists
      const ChecklistTemplate = require("../models/ChecklistTemplate");
      const EmployeeChecklist = require("../models/EmployeeChecklist");
      const template = await ChecklistTemplate.findOne({ type: "Offboarding" });
      if (template) {
        const runTasks = template.tasks.map(t => ({
          taskTitle: t.taskTitle,
          assignedRole: t.assignedRole,
          status: "Pending"
        }));
        await EmployeeChecklist.create({
          employeeId: employee._id,
          type: "Offboarding",
          tasks: runTasks
        });
        console.log(`Offboarding checklist auto-assigned to resigning employee: ${employee.firstName}`);
      }

    } else if (action === 'reject') {
      employee.resignationStatus = 'Rejected';

      if (employee.email) {
        try {
          await sendEmail({
            to: employee.email,
            subject: 'Resignation Request Rejected',
            html: `<p>Dear ${employee.firstName},</p><p>Your resignation request has been declined. Please discuss with the HR / Management.</p>`
          });
        } catch (emailErr) {
          console.error("Email send failed for resignation rejection:", emailErr);
        }
      }
    }

    await employee.save();
    if (isJson) {
      return res.json({ success: true, message: `Resignation successfully ${action}d`, employee });
    }
    res.redirect('/hr/dashboard');

  } catch (err) {
    console.error(err);
    if (isJson) return res.status(500).json({ error: 'Error processing resignation' });
    res.status(500).send('Error processing resignation');
  }
});

/* ==========================
   HR CHANGE PASSWORD
========================== */

// POST /hr/change-password - HR changes their own login password
router.post('/change-password', hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';
  try {
    const { currentPassword, newPassword, confirmPassword } = req.body;

    if (!currentPassword || !newPassword || !confirmPassword) {
      const msg = 'All password fields are required.';
      if (isJson) return res.status(400).json({ error: msg });
      return res.redirect('/hr/settings?pwError=' + encodeURIComponent(msg));
    }

    if (newPassword !== confirmPassword) {
      const msg = 'New password and confirmation do not match.';
      if (isJson) return res.status(400).json({ error: msg });
      return res.redirect('/hr/settings?pwError=' + encodeURIComponent(msg));
    }

    if (newPassword.length < 6) {
      const msg = 'New password must be at least 6 characters long.';
      if (isJson) return res.status(400).json({ error: msg });
      return res.redirect('/hr/settings?pwError=' + encodeURIComponent(msg));
    }

    // System admin (fake userId) cannot change password via this route
    if (req.session.userId === '000000000000000000000000') {
      const msg = 'System admin password is managed via environment variables.';
      if (isJson) return res.status(400).json({ error: msg });
      return res.redirect('/hr/settings?pwError=' + encodeURIComponent(msg));
    }

    const user = await User.findById(req.session.userId);
    if (!user) {
      const msg = 'User account not found.';
      if (isJson) return res.status(404).json({ error: msg });
      return res.redirect('/hr/settings?pwError=' + encodeURIComponent(msg));
    }

    const isMatch = await user.comparePassword(currentPassword);
    if (!isMatch) {
      const msg = 'Current password is incorrect.';
      if (isJson) return res.status(401).json({ error: msg });
      return res.redirect('/hr/settings?pwError=' + encodeURIComponent(msg));
    }

    user.password = newPassword; // Pre-save hook will hash it
    await user.save();

    console.log(`[HR] Password changed for userId: ${req.session.userId}`);
    if (isJson) return res.json({ success: true, message: 'Password updated successfully.' });
    res.redirect('/hr/settings?pwSuccess=true');
  } catch (err) {
    console.error('Error changing HR password:', err);
    if (isJson) return res.status(500).json({ error: 'Failed to change password: ' + err.message });
    res.redirect('/hr/settings?pwError=' + encodeURIComponent(err.message));
  }
});

/* ==========================
   COMPANY & PAYSLIP SETTINGS
========================== */

// GET /hr/settings - View company, geofence, and payslip settings
router.get("/settings", hrAuth, async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json');
  try {
    let settings = await CompanySettings.findOne();
    if (!settings) {
      let defaultName = "My Company";
      if (req.session.tenantId && req.session.tenantId !== 'default') {
        const tenant = await Tenant.findOne({ tenantId: req.session.tenantId });
        if (tenant && tenant.companyName) {
          defaultName = tenant.companyName;
        }
      }
      settings = await CompanySettings.create({
        companyName: defaultName
      });
    }

    if (isJson) {
      return res.json({ success: true, settings });
    }

    res.render("hr/settings", {
      settings,
      success: req.query.success === 'true',
      error: req.query.error || null,
      pwSuccess: req.query.pwSuccess === 'true',
      pwError: req.query.pwError || null
    });
  } catch (err) {
    console.error("Error loading HR settings:", err);
    if (isJson) return res.status(500).json({ error: "Failed to load settings" });
    res.redirect("/hr/dashboard?error=settings_load_failed");
  }
});

// POST /hr/settings - Update company, geofence, and payslip structure settings
router.post("/settings", hrAuth, logoUpload.single("logo"), async (req, res) => {
  const isJson = req.query.format === 'json' || req.headers.accept?.includes('application/json') || req.body.format === 'json';

  // CSRF validation for multipart/form-data (handled here after multer has parsed body)
  if (!isJson) {
    const token = req.body?._csrf || req.query?._csrf || req.headers['x-csrf-token'] || req.headers['csrf-token'];
    if (token && req.session?.csrfToken && token === req.session.csrfToken) {
      // Valid CSRF
    } else if (process.env.NODE_ENV !== 'production' && req.session?.userId) {
      // Allow authenticated user in development
    } else if (!token || token !== req.session?.csrfToken) {
      console.warn(`[CSRF Blocked - Multipart] POST /hr/settings`);
      return res.status(403).send('Forbidden: Invalid CSRF Token');
    }
  }

  try {
    const {
      companyName, tagline, contactEmail, contactPhone, website,
      address, city, state, pincode, country,
      cin, panNumber, gstNumber,
      officeLat, officeLng, officeRadius, officeLocationName, geofenceEnforced,
      currencySymbol, pfPercentage, ptAmount, tdsDefaultPercent,
      payslipNote, signatoryName, signatoryDesignation
    } = req.body;

    const updateData = {
      companyName: companyName ? companyName.trim() : 'HRMS Company',
      tagline: tagline || '',
      contactEmail: contactEmail || '',
      contactPhone: contactPhone || '',
      website: website || '',
      address: address || '',
      city: city || '',
      state: state || '',
      pincode: pincode || '',
      country: country || 'India',
      cin: cin || '',
      panNumber: panNumber || '',
      gstNumber: gstNumber || '',
      officeLat: Number(officeLat) || 19.0597397,
      officeLng: Number(officeLng) || 73.1189947,
      officeRadius: Number(officeRadius) || 200,
      officeLocationName: officeLocationName || 'Headquarters',
      geofenceEnforced: geofenceEnforced === 'true' || geofenceEnforced === true || geofenceEnforced === 'on',
      currencySymbol: currencySymbol || '₹',
      pfPercentage: Number(pfPercentage) || 0,
      ptAmount: Number(ptAmount) || 0,
      tdsDefaultPercent: Number(tdsDefaultPercent) || 0,
      payslipNote: payslipNote || 'This is a computer generated salary statement and does not require a physical signature.',
      signatoryName: signatoryName || 'Authorized Signatory',
      signatoryDesignation: signatoryDesignation || 'HR Operations',
      updatedAt: new Date()
    };

    // If new logo file was uploaded, convert to base64 Data URI
    if (req.file) {
      const mime = req.file.mimetype;
      const b64 = req.file.buffer.toString('base64');
      updateData.logoUrl = `data:${mime};base64,${b64}`;
    } else if (req.body.existingLogoUrl) {
      updateData.logoUrl = req.body.existingLogoUrl;
    }

    const updatedSettings = await CompanySettings.findOneAndUpdate(
      {},
      { $set: updateData },
      { upsert: true, new: true, setDefaultsOnInsert: true }
    );

    // Sync companyName to master Tenant registry if tenantId exists
    if (req.session.tenantId && req.session.tenantId !== 'default' && updateData.companyName) {
      try {
        await Tenant.updateOne(
          { tenantId: req.session.tenantId },
          { $set: { companyName: updateData.companyName } }
        );
      } catch (tenantSyncErr) {
        console.error("Failed to sync company name to master tenant record:", tenantSyncErr);
      }
    }

    if (isJson) {
      return res.json({ success: true, message: "Settings updated successfully", settings: updatedSettings });
    }

    res.redirect("/hr/settings?success=true");
  } catch (err) {
    console.error("Error saving HR settings:", err);
    if (isJson) return res.status(500).json({ error: "Failed to save settings: " + err.message });
    res.redirect("/hr/settings?error=" + encodeURIComponent(err.message));
  }
});

module.exports = router;
