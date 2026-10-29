# Complete HRMS SaaS Platform & AI Suite — User Guide & Architecture Manual

Welcome to the official User Guide and Operational Manual for the **Enterprise Multi-Tenant HRMS SaaS & AI Platform**. This document provides an end-to-end walkthrough of all platform capabilities for System Super-Admins, HR Managers, Department Heads, and Employees across both the **Web Portal** and the **Mobile React Native Application**.

---

## 📋 Table of Contents

1. [Platform Architecture & Multi-Tenant Setup](#1-platform-architecture--multi-tenant-setup)
2. [HR Commander Dashboard & Core Administration](#2-hr-commander-dashboard--core-administration)
3. [AI Resume Screener & Candidate Scrutiny Engine](#3-ai-resume-screener--candidate-scrutiny-engine)
4. [💡 NEW FEATURE IDEA: AI Department Workspaces](#4--new-feature-idea-ai-department-workspaces)
5. [Attendance, Geofencing, Shifts & Roster Management](#5-attendance-geofencing-shifts--roster-management)
6. [Project Timesheets, Expenses & GPS Trip Tracking](#6-project-timesheets-expenses--gps-trip-tracking)
7. [Payroll Processing & Payslip Management](#7-payroll-processing--payslip-management)
8. [Offboarding, Resignations & Permanent Deletion](#8-offboarding-resignations--permanent-deletion)
9. [Mobile Application Operational Guide](#9-mobile-application-operational-guide)
10. [Recommended Roadmap & Next Features](#10-recommended-roadmap--next-features)

---

## 1. Platform Architecture & Multi-Tenant Setup

### Dynamic Database Isolation Per Company
The HRMS utilizes dynamic database multi-tenancy (`utils/tenantManager.js` and `models/`). 
- When a new company registers at `/auth/register-company`, the system automatically provisions an isolated MongoDB database specifically for that tenant (`HRMS_<tenantId>`).
- All company data—employees, attendance logs, candidate resumes, payroll records, and shift rosters—remains completely isolated and encrypted.

### Access Roles
- **Super Admin (`superadmin-server.js`)**: Oversees company registrations, tenant subscriptions, Razorpay billing, and system diagnostics.
- **HR Manager (`/hr/dashboard`)**: Full administrative authority over company employees, payroll, recruitment, appraisals, shift rosters, and employee deletions.
- **Department Manager (`/department/dashboard`)**: Manages department-specific personnel, leaves, timesheets, and checklists.
- **Employee (`/employee/profile`)**: Punch-in/out, apply for leaves, view payslips, submit expenses, log trips, and request resignations.

---

## 2. HR Commander Dashboard & Core Administration

### Navigating the HR Commander (`/hr/dashboard`)
The HR Commander serves as your central control terminal.
- **Live Attendance Telemetry:** Monitor real-time workforce headcount, employees punched in today, shift completion status, and active project tracks.
- **Onboarding New Employees (`/employee/add`):** Manually register new employees with auto-assigned employee codes (`EMPxxxx`), department allocations, salary figures, and default system login credentials (`temp123`).
- **User Directory & Compliance (`/hr/users`):** Inspect user profiles, verify uploaded compliance documents, toggle account access status, and trigger permanent deletions.

---

## 3. AI Resume Screener & Candidate Scrutiny Engine

Located at **`/hr/recruitment`** (accessible via the blue banner on the HR Dashboard).

### Step-by-Step HR Recruitment Workflow:

```
[ Bulk PDF/DOCX Resumes or Text ]
               │
               ▼
   [ AI Scrutiny Engine ]
  (Skills taxonomy, 0-100% score)
               │
               ▼
[ Ranked Candidate Leaderboard ] ──► [ Inspect Competency Report ]
               │
               ▼
 [ 1-Click Employee Onboarding ] ──► [ Active Employee Account Created ]
```

1. **Select Target Role & Department:** Choose from pre-configured positions (e.g. *Software Engineer*, *Full Stack Developer*, *Sales Manager*, *HR Manager*, *Accountant*, *Logistics Manager*) or general roles.
2. **Bulk Upload or Paste Text:**
   - **Bulk Upload:** Drag and drop up to 20 candidate resume files (`PDF`, `DOCX`, `TXT`).
   - **Pasted Text:** Copy and paste raw resume text or CV highlights into the studio.
3. **Run AI Scrutiny:** Click **`[ Run AI Resume Scrutiny ]`**. The weighted AI algorithm computes:
   - **Skill Coverage (40%)**: Compares skills extracted from candidate text against role taxonomy.
   - **Experience Weight (25%)**: Calculates years of domain experience.
   - **Education & Credentials (10-15%)**: Assesses degree qualification level.
   - **Recommendation Badges:** 🟢 `STRONG_HIRE` (85%+), 🔵 `SHORTLIST` (70%+), 🟡 `HOLD` (50%+), 🔴 `REJECT` (<50%).
4. **Ranked Candidate Leaderboard:** Review candidates automatically ranked from highest to lowest score. Use the real-time search bar to filter candidates by skill (e.g. `React`, `Node`, `AWS`).
5. **Inspect Full Report Modal:** Click the eye icon `👁️` to view matched skills, missing criteria, key candidate strengths, and AI executive summaries.
6. **1-Click Candidate Onboarding:** Click **`[ Onboard ]`** to instantly convert the candidate into an active Employee profile with auto-generated login credentials!

---

## 4. 💡 NEW FEATURE IDEA: AI Department Workspaces

To take your HRMS to an enterprise level, we can implement **Departmental AI Workspaces** for each department:

```
                    ┌─────────────────────────────────────────┐
                    │    ENTERPRISE AI DEPARTMENT WORKSPACE    │
                    └────────────────────┬────────────────────┘
                                         │
     ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
     ▼                   ▼                               ▼                   ▼
┌─────────┐        ┌──────────┐                    ┌───────────┐       ┌───────────┐
│   IT    │        │    HR    │                    │   SALES   │       │ ACCOUNTS  │
│ WORKSPACE│        │ WORKSPACE│                    │ WORKSPACE │       │ WORKSPACE │
└────┬────┘        └────┬─────┘                    └─────┬─────┘       └─────┬─────┘
     │                  │                                │                   │
 • Code Audit       • Policy Q&A                     • Pitch Generator   • Invoice OCR
 • Access Logs      • Exit Analysis                  • Deal Pipeline     • GST Calculator
 • IT Asset Tracker • Appraisal Copilot              • Lead Scoring      • Expense Audit
```

### Specialized Capabilities per Department Workspace:
1. **IT AI Workspace (`/department/it/workspace`)**:
   - Automated IT Asset allocation & laptop inventory tracking.
   - Incident ticket auto-summarization and system access auditing.
2. **HR AI Workspace (`/department/hr/workspace`)**:
   - Natural Language HR Policy Q&A assistant for instant answers on leaves, gratuity, and insurance.
   - Exit Interview Sentiment Analyzer & Performance Review Copilot.
3. **Sales AI Workspace (`/department/sales/workspace`)**:
   - AI Lead Scoring & Client Proposal Generator.
   - Target vs. Achievement projection analytics.
4. **Accounts & Finance AI Workspace (`/department/accounts/workspace`)**:
   - Automated Invoice & Expense Receipt OCR text extraction.
   - GST, TDS deduction calculator & anomalies auditor.
5. **Logistics & Operations AI Workspace (`/department/logistics/workspace`)**:
   - Route optimization recommendations for field delivery trips.
   - Fleet maintenance alerts & inventory re-order predictions.

---

## 5. Attendance, Geofencing, Shifts & Roster Management

- **Location-Optional Punch In (`/attendance/location-optional-punch-in`)**: Allows WFH or remote field employees to record attendance with optional coordinates and reason notes.
- **Shift Configurations (`/hr/shifts`)**: Create custom morning, afternoon, night, or rotational shifts with grace periods and late thresholds.
- **Roster Calendar (`/hr/roster`)**: Assign weekly employee shifts and manage swap requests.

---

## 6. Project Timesheets, Expenses & GPS Trip Tracking

- **Project Timesheets (`/hr/timesheets`)**: Assign employees to client delivery projects, track logged hours, and review milestone completions.
- **GPS Trip Tracking (`/trip/hr/dashboard`)**: Real-time GPS coordinate mapping for field visits, client meetings, and travel allowance calculations.
- **Expense Receipts (`/expense/hr/dashboard`)**: Upload digital receipts, categorize expenses, and trigger one-click approval workflows.

---

## 7. Payroll Processing & Payslip Management

- **Manage Payslips (`/payslip/hr/payslips`)**: Select month/year, automatically compile salary components (Base, HRA, Travel Allowance, LOP deductions, Income Tax, PF), and generate downloadable PDF payslips for employees.

---

## 8. Offboarding, Resignations & Permanent Deletion

### Resignation & Offboarding Workflow
1. Employee submits resignation via Profile (`/employee/profile`).
2. HR/Manager receives immediate notification and reviews the pending request on the HR Commander Dashboard.
3. Upon acceptance, an automated **Offboarding Checklist** (Exit Interview, Asset Return, System Access Revocation, Final Settlement) is triggered.

### Permanent Employee Deletion (HR Only)
For employees whose status is **`Terminated`**, **`Resigned`**, or **`Inactive`**:
1. Open **Manage User Profiles** (`/hr/users`) or **Edit Employee** (`/employee/edit/:id`).
2. Set the status to `Terminated` if not already set.
3. Scroll to the **Danger Zone** section and click **`[ Delete Completely ]`**.
4. Confirm the warning prompt to permanently erase the employee record and login account from MongoDB.

---

## 9. Mobile Application Operational Guide

The React Native mobile application provides on-the-go access for both HR and Employees:

- **Biometric / GPS Punch In**: Geofenced location verification with fallback WFH reason notes.
- **Mobile AI Resume Screener (`HRRecruitmentScreen.js`)**:
  - **AI Screener Tab:** Input candidate resume text and calculate 0–100% match scores on mobile.
  - **Ranked Pipeline Tab:** View candidate rankings and tap **`+ Onboard`** for instant hiring.
  - **Quick Add Tab:** Onboard new employees directly from your mobile device.
- **Expenses & Trip Logging**: Snap photos of expense receipts and track travel routes with coordinates.

---

## 10. Recommended Roadmap & Next Features

| Priority | Feature Module | Strategic Value |
|---|---|---|
| 🔥 **High** | **AI Department Workspaces** | Specialized AI assistants for IT, HR, Sales, Accounts & Logistics. |
| 🔥 **High** | **Automated WhatsApp / SMS Alerts** | Send automated interview invites, payslips, & shift reminders directly to mobile. |
| ⚡ **Medium** | **Biometric Hardware API Integration** | Connect physical finger-print & face-recognition devices directly to the attendance engine. |
| ⚡ **Medium** | **Custom Job Description (JD) Builder** | Allow HR to paste custom JD text to generate custom match scoring criteria on the fly. |

---

## 11. Advanced Enterprise & AI Architecture Documentation
For complete technical specifications, schemas, API endpoints, and workflows for **AI Workspaces**, the **Recruiter Interview Bot**, **Team Chat**, **Celebrations & Kudos Hub**, and **Salary Hike Management**, consult the dedicated manual:
👉 [HRMS Advanced Features & AI Workspace Manual](file:///Users/akashd/Documents/PROJECTS/HRMS/HRMS/HRMS_ADVANCED_FEATURES_AND_AI_WORKSPACE_MANUAL.md)

---

## 12. Legal, Data Privacy & Limitation of Liability Agreement
For the official multi-page Master SaaS Agreement, Data Privacy Policy (DPDP Act 2023 & GDPR), Non-Sharing Commitment, and Comprehensive Limitation of Liability shielding the platform against legal allegations, consult the binding legal document:
👉 [Enterprise Master Subscription Agreement & Data Privacy Policy](file:///Users/akashd/Documents/PROJECTS/HRMS/HRMS/HRMS_LEGAL_DATA_PRIVACY_AND_TERMS_OF_SERVICE.md)

---

*Documentation Version 2.4 • HRMS Enterprise Suite • Generated for Multi-Tenant Platform Deployment*

