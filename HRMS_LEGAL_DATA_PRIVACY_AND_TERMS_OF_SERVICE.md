# HRMS ENTERPRISE MASTER SUBSCRIPTION AGREEMENT, DATA PRIVACY & LIMITATION OF LIABILITY FRAMEWORK

**Document Version:** 2.4 (Enterprise Edition)  
**Applicability:** Multi-Tenant Cloud HRMS Platform (SaaS)  
**Governing Standard:** Information Technology Act (2000), Digital Personal Data Protection (DPDP) Act 2023, and Global SaaS Regulatory Standards.

---

## TABLE OF CONTENTS
1. [Preamble & Acceptance of Terms](#1-preamble--acceptance-of-terms)
2. [Definitions & Interpretations](#2-definitions--interpretations)
3. [Data Ownership, Privacy & Non-Sharing Commitment](#3-data-ownership-privacy--non-sharing-commitment)
4. [Data Security Architecture & Cryptographic Protocols](#4-data-security-architecture--cryptographic-protocols)
5. [The Shared Responsibility Security Model](#5-the-shared-responsibility-security-model)
6. [Disclaimer of Warranties ("AS IS" & "AS AVAILABLE")](#6-disclaimer-of-warranties-as-is--as-available)
7. [Comprehensive Limitation of Liability & Exclusion of Damages](#7-comprehensive-limitation-of-liability--exclusion-of-damages)
8. [Indemnification & Hold-Harmless Defense](#8-indemnification--hold-harmless-defense)
9. [Labor Law, Tax & Statutory Compliance Disclaimer](#9-labor-law-tax--statutory-compliance-disclaimer)
10. [Data Backup, Business Continuity & Disaster Recovery](#10-data-backup-business-continuity--disaster-recovery)
11. [Data Retention, Portability & Deletion Protocols](#11-data-retention-portability--deletion-protocols)
12. [Service Levels, Maintenance & Upstream Provider Exclusions](#12-service-levels-maintenance--upstream-provider-exclusions)
13. [Security Incident Management & Notification](#13-security-incident-management--notification)
14. [Governing Law, Mandatory Arbitration & Jurisdiction](#14-governing-law-mandatory-arbitration--jurisdiction)
15. [Execution & Tenant Acknowledgment Schedule](#15-execution--tenant-acknowledgment-schedule)

---

## 1. PREAMBLE & ACCEPTANCE OF TERMS

This Master Subscription Agreement, Data Privacy Policy, and Limitation of Liability Framework ("**Agreement**") constitutes a legally binding contract between:

1. **The Software Provider / Platform Licensor ("Provider", "We", "Us", or "Our")**, owning and operating the proprietary multi-tenant Human Resource Management System ("**HRMS**" or "**Platform**"); and
2. **The Subscribing Entity / Client Organization ("Customer", "Tenant", "Client", or "You")**, accessing or utilizing the Platform on behalf of itself, its subsidiaries, contractors, and authorized employees.

### 1.1 Binding Acceptance
BY ACCESSING, DEPLOYING, CREATING A TENANT DATABASE, OR PERMITTING EMPLOYEES TO ACCESS THE HRMS PLATFORM, CUSTOMER UNCONDITIONALLY AGREES TO BE BOUND BY EVERY CLAUSE, DISCLAIMER, AND LIMITATION OF LIABILITY OUTLINED IN THIS AGREEMENT. IF CUSTOMER DOES NOT AGREE WITH EVERY TERM, CUSTOMER MUST IMMEDIATELY CEASE USAGE AND TRANSMIT WRITTEN TERMINATION NOTICE.

---

## 2. DEFINITIONS & INTERPRETATIONS

* **"Customer Data":** All digital information, employee dossiers, biometric/punch records, salary breakdowns, leave applications, documents (Aadhaar, PAN, passports, contracts), trip logs, appraisals, and tickets uploaded or generated in Customer's dedicated tenant database.
* **"Data Fiduciary" / "Data Controller":** The Customer organization, which determines the purpose, legal basis, and means of processing its employees' personal data.
* **"Data Processor":** The Provider, which provides cloud infrastructure, computational engines, and database interfaces solely to process data under Customer’s direction.
* **"Tenant Isolation":** The architectural partitioning ensuring that Customer's database schemas, session stores, and document assets remain segregated and inaccessible to other organizations using the SaaS platform.
* **"Force Majeure Event":** Any event beyond the reasonable control of the Provider, including but not limited to catastrophic failures of Tier-1 public cloud providers (e.g., AWS, Microsoft Azure, Google Cloud), telecommunications backbone disruptions, cyber-warfare, zero-day exploit vulnerabilities, governmental orders, or acts of God.

---

## 3. DATA OWNERSHIP, PRIVACY & NON-SHARING COMMITMENT

### 3.1 100% Customer Data Ownership
Provider explicitly acknowledges and agrees that:
* **The Customer retains exclusive, sole, and unencumbered ownership of all Customer Data.**
* Provider claims no intellectual property, proprietary interest, or title over Customer Data, employee profiles, payroll numbers, or corporate policies uploaded to the system.

### 3.2 Strict Non-Monetization & Non-Sharing Guarantee
Provider solemnly covenants that:
* **NO SALE OF DATA:** Provider will NEVER sell, lease, monetize, license, or trade Customer Data to third-party data brokers, marketing agencies, advertisers, or credit bureaus.
* **NO DATA HARVESTING:** Provider will not index, mine, or scrape employee records for commercial analytics or advertising targeting.
* **RESTRICTED SYSTEM ACCESS:** Provider’s system engineers and operations personnel are strictly prohibited from viewing or accessing Customer Data, except:
  1. Under express written instruction from Customer’s authorized administrator for debugging purposes;
  2. To prevent or resolve critical technical infrastructure outages; or
  3. When strictly required by a final, unappealable subpoena or court order issued by a court of competent jurisdiction.

### 3.3 Authorized Infrastructure Sub-Processors
Customer grants permission for Provider to utilize enterprise-grade sub-processors strictly for hosting and operating the service:

| Sub-Processor Category | Enterprise Vendors Utilized | Purpose | Security Standard |
| :--- | :--- | :--- | :--- |
| **Compute & Cloud Hosting** | Amazon Web Services (AWS) / DigitalOcean / Render | Server runtime, application delivery | SOC 2 Type II, ISO 27001 |
| **Encrypted Database Hosting** | MongoDB Atlas Enterprise Cloud | Tenant data storage, automated replication | SOC 2, HIPAA, ISO 27001 |
| **Transactional Messaging** | Resend / SendGrid / Twilio | Password resets, payslip delivery | TLS 1.3 encrypted transit |
| **Subscription Billing** | Razorpay / Stripe Payments | Tenant renewal billing | PCI-DSS Level 1 Compliant |

All sub-processors are bound by enterprise data protection agreements that enforce security measures no less protective than those defined in this Agreement.

---

## 4. DATA SECURITY ARCHITECTURE & CRYPTOGRAPHIC PROTOCOLS

Provider implements industry-standard administrative, physical, and technical safeguards designed to preserve the integrity, confidentiality, and availability of Customer Data:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      DATA SECURITY IN-DEPTH MATRIX                     │
├───────────────────────┬────────────────────────────────────────────────┤
│ Transit Security      │ End-to-End TLS 1.3 / HTTPS 256-Bit SSL         │
├───────────────────────┼────────────────────────────────────────────────┤
│ Storage Encryption    │ AES-256 Bit Encryption At-Rest (Database + S3) │
├───────────────────────┼────────────────────────────────────────────────┤
│ Credential Protection │ Salted BCrypt Hash (Rounds >= 10) for Passwords│
├───────────────────────┼────────────────────────────────────────────────┤
│ Isolation Level       │ Tenant Proxy Middleware Dynamic Route Scoping  │
├───────────────────────┼────────────────────────────────────────────────┤
│ Privilege Controls    │ Role-Based Access Control (RBAC: HR, Mgr, Emp) │
└───────────────────────┴────────────────────────────────────────────────┘
```

### 4.1 Cryptographic Standards
* **Data-in-Transit:** All communication across client browsers, mobile applications, AI microservices, and Node.js servers is enforced through TLS 1.3 using modern cipher suites. Insecure HTTP connections are forcibly upgraded or rejected.
* **Data-at-Rest:** All database volumes, object stores, and disk snapshots are encrypted using Advanced Encryption Standard (AES) with 256-bit keys managed via dedicated Hardware Security Modules (KMS).
* **Password Non-Recoverability:** User passwords are never stored in plaintext or reversible encryption. Passwords undergo cryptographic salting and iterative one-way hashing (`bcrypt`).

### 4.2 Multi-Tenant Logical Segregation
* Every database request passes through Provider's tenant connection proxy (`utils/tenantModel.js`), which resolves tenant tenancy keys dynamically from secure session headers.
* No tenant is capable of querying, updating, or viewing records from any other tenant workspace.

---

## 5. THE SHARED RESPONSIBILITY SECURITY MODEL

Cloud security is a collaborative obligation. The following **Shared Responsibility Model** delineates the boundaries of liability between Provider and Customer:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SHARED RESPONSIBILITY MATRIX                         │
├───────────────────────────────────┬────────────────────────────────────┤
│       PROVIDER RESPONSIBILITY     │      CUSTOMER RESPONSIBILITY       │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Platform Codebase & Patches     │ • Master Admin Credential Hygiene  │
│ • Cloud Infrastructure Firewalls  │ • Strong Password Policies         │
│ • Database Partitioning Logic     │ • Revoking Departed Employee Access│
│ • Encryption at Rest & Transit    │ • Local Device & Anti-Virus Health │
│ • AI Service Infrastructure       │ • Accuracy of Salary & Tax Inputs  │
│ • Automated Data Backups          │ • Employee Consent for Geotracking │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 5.1 Customer's Affirmative Obligations
Customer explicitly agrees that it is exclusively responsible for:
1. **Credential Safeguarding:** Ensuring that all HR admins, managers, and employees maintain confidential passwords and do not share accounts.
2. **Access Revocation:** Promptly updating employee status to `"Resigned"` or `"Inactive"` immediately upon termination of any staff member to terminate their platform access.
3. **Endpoint Protection:** Maintaining updated antivirus, firewall, and operating system software on devices used by employees to access the HRMS.
4. **Lawful Data Collection & Consent:** Procuring all necessary employee consents required under applicable privacy statutes (e.g., DPDP Act 2023) prior to uploading identity documents (Aadhaar, PAN, Passports), tracking live business trips, or recording clock punches.

---

## 6. DISCLAIMER OF WARRANTIES ("AS IS" & "AS AVAILABLE")

### 6.1 General Disclaimer
EXCEPT AS EXPRESSLY SET FORTH IN THIS AGREEMENT, THE HRMS PLATFORM, INCLUDING ALL WEB MODULES, MOBILE INTERFACES, AI ASSISTANTS, AND PAYROLL CALCULATORS, IS PROVIDED STRICTLY ON AN **"AS IS"** AND **"AS AVAILABLE"** BASIS.

### 6.2 No Guarantees
TO THE MAXIMUM EXTENT PERMITTED UNDER APPLICABLE LAW, PROVIDER DISCLAIMS ALL WARRANTIES, WHETHER STATUTORY, EXPRESS, OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
* ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT;
* ANY WARRANTY THAT THE PLATFORM WILL MEET CUSTOMER'S UNIQUE INTERNAL SPECIFICATIONS;
* ANY WARRANTY THAT PLATFORM ACCESS WILL BE 100% UNINTERRUPTED, BUG-FREE, SECURE FROM ADVANCED ZERO-DAY CYBER-ATTACKS, OR TOTALLY ERROR-FREE;
* ANY WARRANTY REGARDING THE SPEED, ACCURACY, OR DELAYS OF THIRD-PARTY NETWORKS (CELLULAR CARRIERS, GPS SATELLITES, OR INTERNET SERVICE PROVIDERS).

---

## 7. COMPREHENSIVE LIMITATION OF LIABILITY & EXCLUSION OF DAMAGES

> **IMPORTANT NOTICE:** THIS SECTION CONSTITUTES AN ESSENTIAL BASIS OF THE COMMERCIAL BARGAIN BETWEEN THE PARTIES. IN THE ABSENCE OF THESE LIMITATIONS, THE PRICING FOR THE PLATFORM WOULD BE SUBSTANTIALLY HIGHER.

### 7.1 Aggregate Financial Liability Cap
**TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL PROVIDER’S TOTAL, CUMULATIVE, AGGREGATE FINANCIAL LIABILITY ARISING OUT OF OR RELATING TO THIS AGREEMENT, WHETHER IN CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF STATUTORY DUTY, INDEMNITY, OR OTHERWISE, EXCEED:**
* **THE TOTAL SUBSCRIPTION FEES ACTUALLY PAID BY CUSTOMER TO PROVIDER IN THE THREE (3) MONTHS IMMEDIATELY PRECEDING THE OCCURRENCE GIVING RISE TO LIABILITY; OR**
* **INR 10,000 (TEN THOUSAND INDIAN RUPEES) / USD $120,**  
**WHICHEVER AMOUNT IS LESS.**

### 7.2 Total Exclusion of Indirect & Consequential Damages
**UNDER NO CIRCUMSTANCES SHALL PROVIDER, ITS FOUNDERS, DEVELOPERS, AFFILIATES, OR LICENSORS BE LIABLE TO CUSTOMER OR ANY THIRD PARTY FOR:**
1. **LOSS OF BUSINESS PROFITS, REVENUE, CONTRACTS, OR COMMERCIAL OPPORTUNITY;**
2. **BUSINESS INTERRUPTION, SHUTDOWN, WORK STOPPAGE, OR LOSS OF WORKFORCE PRODUCTIVITY;**
3. **LOSS, CORRUPTION, DESTRUCTION, OR ALTERATION OF DIGITAL RECORDS OR CUSTOMER DATA;**
4. **COSTS OF PROCUREMENT OF SUBSTITUTE HARDWARE, SERVICES, OR SOFTWARE;**
5. **ANY SPECIAL, INDIRECT, INCIDENTAL, PUNITIVE, EXEMPLARY, OR CONSEQUENTIAL DAMAGES WHATSOEVER, EVEN IF PROVIDER HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.**

### 7.3 Complete Immunity Regarding External & Client-Side Breaches
Provider shall have **ABSOLUTE ZERO LEGAL LIABILITY** for any data loss, data compromise, unauthorized leak, or disruption caused in whole or in part by:
* **Compromised Credentials:** Phishing, keylogging, weak passwords, or employee negligence on Customer’s devices;
* **Internal Rogue Actors:** Unauthorized data viewing or export carried out by Customer’s own employees, HR managers, or administrators;
* **Third-Party Upstream Outages:** Outages, network partitions, or data center failures experienced by Tier-1 cloud providers (AWS, MongoDB Atlas, Cloudflare, Razorpay);
* **Internet Backbone Disruptions:** Fiber cuts, telecom carrier DNS failures, or local power grid blackouts;
* **Zero-Day Vulnerabilities:** Novel operating system or cryptographic vulnerabilities that could not have been mitigated by commercially reasonable software patch standards.

---

## 8. INDEMNIFICATION & HOLD-HARMLESS DEFENSE

### 8.1 Customer’s Indemnification of Provider
Customer agrees to defend, indemnify, and hold harmless Provider, its officers, directors, software engineers, affiliates, and agents against any and all third-party lawsuits, claims, proceedings, regulatory fines, penalties, settlements, and legal defense costs (including attorney fees) arising from:
1. **Labor & Employment Disputes:** Any dispute, lawsuit, or arbitration between Customer and its current or former employees (including wrongful termination, unpaid overtime, sexual harassment, discrimination, or salary calculation disputes);
2. **Unlawful Surveillance / Geolocation Claims:** Any claim by Customer’s employees alleging unlawful monitoring, invasion of privacy, or labor violations resulting from Customer’s use of the Live Trip Tracker, GPS punch clock, or map telemetry;
3. **Privacy Statute Violations:** Customer’s failure to secure valid, informed employee consent prior to collecting identity proofs (Aadhaar, PAN, Passport, Bank Details) under applicable data protection legislation;
4. **Customer Data Infringement:** Any claim that Customer Data violates third-party copyright, trade secret, or privacy rights.

---

## 9. LABOR LAW, TAX & STATUTORY COMPLIANCE DISCLAIMER

### 9.1 Computational Tool Only
Customer acknowledges that:
* The HRMS platform provides computational, mathematical, and record-keeping software tools (e.g., calculating PF, Professional Tax, TDS deductions, CTC simulations, and Loss-of-Pay adjustments).
* **Provider is NOT a chartered accountancy firm, legal counsel, or tax advisory service.**
* Customer remains solely and exclusively responsible for verifying the legal correctness of salary structures, minimum wage laws, tax withholding, and labor compliances in Customer's operating jurisdictions.
* Provider bears no liability for tax penalties, labor tribunal judgments, or statutory interest levied against Customer by any governmental authority.

---

## 10. DATA BACKUP, BUSINESS CONTINUITY & DISASTER RECOVERY

### 10.1 Automated Rolling Backups
* Provider configures automated daily rolling snapshots for all production tenant databases.
* Snapshots are encrypted and geographically replicated across distinct cloud availability zones.

### 10.2 Customer Backup Responsibility
Notwithstanding Provider's operational backups:
* Customer is encouraged to regularly export its employee directories, monthly attendance sheets, and payroll registers using built-in CSV/Excel export tools.
* In the event of catastrophic data corruption, Provider’s sole liability shall be commercially reasonable efforts to restore data from the latest available operational backup snapshot.

---

## 11. DATA RETENTION, PORTABILITY & DELETION PROTOCOLS

### 11.1 Active Subscription
Customer Data remains accessible 24/7 throughout the term of an active, fully-paid subscription.

### 11.2 Post-Termination Grace Period (30 Days)
Upon expiration or cancellation of Customer’s subscription:
* Customer’s workspace transitions to `"Read-Only / Export"` mode for a duration of **thirty (30) calendar days**.
* During this grace period, Customer’s authorized administrator may download all employee reports, attendance files, and documents.

### 11.3 Irreversible Data Purging (60 Days)
* Following the expiration of sixty (60) calendar days from subscription termination, Provider’s automated background purge jobs will permanently delete Customer’s tenant database, collections, and media files from live disks.
* Once purged, Customer Data cannot be recovered or reconstituted.

---

## 12. SERVICE LEVELS, MAINTENANCE & UPSTREAM PROVIDER EXCLUSIONS

### 12.1 Target Availability
Provider targets a baseline service availability of **99.5% Uptime** during standard business operations, calculated monthly.

### 12.2 Scheduled Maintenance
* Provider reserves the right to perform scheduled system upgrades, security patches, and database optimizations between 00:00 and 04:00 IST (Indian Standard Time).
* Provider will make reasonable efforts to announce scheduled downtime via in-app broadcast banners at least 24 hours in advance.

### 12.3 Downtime Exclusions
Service availability calculations strictly exclude downtime caused by:
1. Customer’s internal internet connectivity, proxy, or ISP failures;
2. Cloud infrastructure degradation reported by public status pages of AWS or MongoDB Atlas;
3. Force Majeure Events, cyber warfare, or emergency maintenance required to address critical vulnerabilities.

---

## 13. SECURITY INCIDENT MANAGEMENT & NOTIFICATION

### 13.1 Incident Response Protocol
In the event of a verified, unauthorized third-party penetration of Provider’s core infrastructure that directly compromises Customer's unencrypted personal records:
1. Provider will immediately isolate the affected systems and invoke remediation protocols.
2. Provider will notify Customer’s designated primary administrator via email within **seventy-two (72) hours** of confirming the incident.
3. Provider will provide an executive incident report detailing the nature of the breach, the affected data scopes, and the corrective measures deployed.

### 13.2 Non-Actionable Events
Routine, unsuccessful attacks against Provider’s perimeter firewalls (e.g., automated port scans, brute-force password attempts blocked by rate limiters, or DDoS attacks absorbed by Cloudflare) do not constitute a reportable incident.

---

## 14. GOVERNING LAW, MANDATORY ARBITRATION & JURISDICTION

### 14.1 Governing Law
This Agreement shall be construed, interpreted, and governed in accordance with the substantive laws of **India**, without regard to conflict of laws principles.

### 14.2 Good-Faith Conciliation
In the event of any controversy, claim, or dispute arising out of or relating to this Agreement, the authorized representatives of both parties shall first engage in good-faith executive negotiations for a period of not less than thirty (30) days.

### 14.3 Mandatory Binding Arbitration
* If the dispute is not resolved through conciliation, it shall be referred to and finally resolved by **binding arbitration** in accordance with the **Arbitration and Conciliation Act, 1996** (as amended).
* The arbitral tribunal shall consist of a sole arbitrator mutually appointed by the parties, or failing agreement, appointed in accordance with the Act.
* The seat and venue of arbitration shall be **New Delhi, India**.
* The arbitral proceedings shall be conducted in the **English language**, and the arbitral award shall be final, non-appealable, and enforceable in any court of competent jurisdiction.

### 14.4 Exclusive Judicial Jurisdiction & Class Action Waiver
* Subject to Section 14.3, the Courts situated in **New Delhi, India** shall have exclusive territorial jurisdiction over any legal matters arising from this Agreement.
* **CLASS ACTION WAIVER:** ALL CLAIMS MUST BE BROUGHT IN AN INDIVIDUAL CAPACITY, AND NOT AS A PLAINTIFF OR CLASS MEMBER IN ANY PURPORTED CLASS, COLLECTIVE, OR REPRESENTATIVE PROCEEDING.

---

## 15. EXECUTION & TENANT ACKNOWLEDGMENT SCHEDULE

Customer acknowledges that digital acceptance during tenant registration, clicking *"I Agree to Terms"*, or entering payment details for subscription renewal constitutes a valid, legally enforceable electronic signature under Section 10A of the Information Technology Act, 2000.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      TENANT SUBSCRIPTION SCHEDULE                      │
├───────────────────────┬────────────────────────────────────────────────┤
│ Tenant Organization   │ [Populated Automatically on Workspace Creation]│
├───────────────────────┼────────────────────────────────────────────────┤
│ Tenant Subdomain/Slug │ [tenant_slug].hrmsplatform.com                 │
├───────────────────────┼────────────────────────────────────────────────┤
│ Designated Admin Email│ [admin@company.com]                            │
├───────────────────────┼────────────────────────────────────────────────┤
│ Legal Tier & Scope    │ Multi-Tenant Enterprise SaaS Framework         │
├───────────────────────┼────────────────────────────────────────────────┤
│ Electronic Acceptance │ Confirmed via Cryptographic Session Token      │
└───────────────────────┴────────────────────────────────────────────────┘
```

**[END OF ENTERPRISE MASTER SUBSCRIPTION AGREEMENT & DATA PRIVACY FRAMEWORK]**
