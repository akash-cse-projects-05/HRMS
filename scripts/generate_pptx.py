import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # blank layout

    # Color Palette
    BG_COLOR = RGBColor(11, 15, 25)         # #0B0F19 Dark Navy
    CARD_BG = RGBColor(19, 27, 46)          # #131B2E Card Dark
    CARD_BORDER = RGBColor(40, 53, 80)      # Border
    TEXT_WHITE = RGBColor(248, 250, 252)    # Title White
    TEXT_MUTED = RGBColor(148, 163, 184)    # Slate Muted
    ACCENT_BLUE = RGBColor(59, 130, 246)    # Electric Blue
    ACCENT_CYAN = RGBColor(6, 182, 212)     # Cyan
    ACCENT_GREEN = RGBColor(16, 185, 129)   # Emerald Green
    ACCENT_AMBER = RGBColor(245, 158, 11)   # Amber Gold
    ACCENT_PURPLE = RGBColor(139, 92, 246)  # Purple

    def set_slide_background(slide):
        bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = BG_COLOR
        bg_shape.line.fill.background()
        return bg_shape

    def add_header(slide, eyebrow_text, title_text, subtitle_text=""):
        # Eyebrow
        eb_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        eb_tf = eb_box.text_frame
        eb_tf.word_wrap = True
        p_eb = eb_tf.paragraphs[0]
        p_eb.text = eyebrow_text.upper()
        p_eb.font.size = Pt(11)
        p_eb.font.bold = True
        p_eb.font.color.rgb = ACCENT_CYAN
        p_eb.font.name = "Calibri"

        # Title
        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.9))
        t_tf = t_box.text_frame
        t_tf.word_wrap = True
        p_t = t_tf.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(26)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.font.name = "Calibri"

        # Subtitle
        if subtitle_text:
            s_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.55), Inches(11.7), Inches(0.6))
            s_tf = s_box.text_frame
            s_tf.word_wrap = True
            p_s = s_tf.paragraphs[0]
            p_s.text = subtitle_text
            p_s.font.size = Pt(13)
            p_s.font.color.rgb = TEXT_MUTED
            p_s.font.name = "Calibri"

    def add_card(slide, left, top, width, height, title, body_text="", tag="", tag_color=ACCENT_BLUE):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.25)
        tf.margin_bottom = Inches(0.25)

        if tag:
            p_tag = tf.paragraphs[0]
            p_tag.text = tag.upper()
            p_tag.font.size = Pt(10)
            p_tag.font.bold = True
            p_tag.font.color.rgb = tag_color
            p_tag.font.name = "Calibri"
            p_title = tf.add_paragraph()
        else:
            p_title = tf.paragraphs[0]

        p_title.text = title
        p_title.font.size = Pt(15)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE
        p_title.font.name = "Calibri"

        if body_text:
            p_body = tf.add_paragraph()
            p_body.text = body_text
            p_body.font.size = Pt(12)
            p_body.font.color.rgb = TEXT_MUTED
            p_body.font.name = "Calibri"

        return card

    # ==========================================
    # SLIDE 1: Title & Vision
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)
    
    # Hero Title Box
    h_box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.3), Inches(2.2))
    h_tf = h_box.text_frame
    h_tf.word_wrap = True
    p1 = h_tf.paragraphs[0]
    p1.text = "AURA HRMS ENTERPRISE"
    p1.font.size = Pt(14)
    p1.font.bold = True
    p1.font.color.rgb = ACCENT_CYAN

    p2 = h_tf.add_paragraph()
    p2.text = "Next-Gen Workforce Operating System"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE

    p3 = h_tf.add_paragraph()
    p3.text = "Unified Web Portal + Native iOS & Android Mobile Suite + Automated Indian Statutory Payroll"
    p3.font.size = Pt(16)
    p3.font.color.rgb = TEXT_MUTED

    # 4 Highlights
    add_card(slide1, Inches(1.0), Inches(3.8), Inches(2.6), Inches(2.8), "Automated Payroll", "Auto-calculates PF, PT, TDS & Loss-of-Pay (LOP) with single-click digital bulk payslip generation.", "100% Turnkey", ACCENT_GREEN)
    add_card(slide1, Inches(3.9), Inches(3.8), Inches(2.6), Inches(2.8), "Live Field Telemetry", "Interactive satellite route tracking, GPS check-ins, and direct travel expense receipt linkage.", "Live GPS Map", ACCENT_BLUE)
    add_card(slide1, Inches(6.8), Inches(3.8), Inches(2.6), Inches(2.8), "Native Mobile App", "Geofenced punches, leave applications, instant payslip downloads, and real-time push alerts.", "iOS & Android", ACCENT_PURPLE)
    add_card(slide1, Inches(9.7), Inches(3.8), Inches(2.6), Inches(2.8), "Bank-Grade Privacy", "DPDP Act 2023 certified tenant-isolated databases with zero third-party data sharing guarantee.", "100% Isolated", ACCENT_AMBER)

    # ==========================================
    # SLIDE 2: The Core Problem
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "The Industry Pain Point", "Why Legacy HR & Payroll Systems are Broken & Bloated", "Growing organizations lose 40+ hours every month juggling disconnected tools, manual spreadsheets, and opaque enterprise software.")
    
    add_card(slide2, Inches(0.8), Inches(2.5), Inches(3.6), Inches(4.2), "Fragmented Tool Sprawl", "Biometrics on one physical device, leaves over email, travel expense receipts on WhatsApp, and monthly payroll calculated on Excel. Nothing connects, leading to costly human errors and delayed salaries.", "Operational Chaos", RGBColor(239, 68, 68))
    add_card(slide2, Inches(4.8), Inches(2.5), Inches(3.6), Inches(4.2), "Costly Enterprise Lock-In", "Legacy platforms like Darwinbox and Keka force high minimum contract fees (Rs 1L - 10L/year) with 3 to 6 months of painful setup and rigid, clunky user interfaces that employees hate using.", "Budget Drain", RGBColor(239, 68, 68))
    add_card(slide2, Inches(8.8), Inches(2.5), Inches(3.6), Inches(4.2), "Blind Spot in Field Staff", "Zero visibility into sales executive visits, site engineering trips, or client travels. Managers blindly approve reimbursement claims with no GPS verification or proof of visit.", "Financial Leakage", RGBColor(239, 68, 68))

    # ==========================================
    # SLIDE 3: The Unified Ecosystem Solution
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "The All-In-One Solution", "One Unified Platform: Web Dashboard + Native Mobile App + AI", "Everything your workforce needs from hire to retire in one seamless, high-performance ecosystem.")

    add_card(slide3, Inches(0.8), Inches(2.5), Inches(2.7), Inches(4.2), "1. Attendance & Shifts", "• 1-Tap Geofenced Mobile Punch\n• Biometric Hardware Sync\n• Multi-Shift Dynamic Rostering\n• Regularization Approval Flow\n• Real-Time Headcount Monitor", "Discipline & Time", ACCENT_CYAN)
    add_card(slide3, Inches(3.8), Inches(2.5), Inches(2.7), Inches(4.2), "2. Statutory Payroll", "• Automated PF & Professional Tax\n• Dynamic Loss-of-Pay (LOP) Cuts\n• CTC Breakdown & Tax Slabs\n• Single-Click Bulk Payslip Batch\n• Encrypted PDF Payslip Delivery", "100% Compliant", ACCENT_GREEN)
    add_card(slide3, Inches(6.8), Inches(2.5), Inches(2.7), Inches(4.2), "3. Live Field Travel", "• GPS Route Monitoring & Telemetry\n• Interactive HR Satellite Map\n• Official Trip Logs & Dossiers\n• Camera Receipt Reimbursements\n• Real-Time Expense Linkage", "Field Transparency", ACCENT_BLUE)
    add_card(slide3, Inches(9.8), Inches(2.5), Inches(2.7), Inches(4.2), "4. PMS & Growth", "• Quarterly OKRs & Key Milestones\n• 2-Stage Appraisal Reviews\n• 360 Monthly Review Dossier\n• Real-Time CTC Hike Simulator\n• Branded Increment Letters", "Talent Retention", ACCENT_PURPLE)

    # ==========================================
    # SLIDE 4: Native Mobile Application Showcase
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "Mobile-First Experience", "Native iOS & Android Mobile Application", "Your employees carry their office, attendance, leaves, and payslips right in their pockets.")

    add_card(slide4, Inches(0.8), Inches(2.5), Inches(5.6), Inches(2.0), "1-Tap Geofenced Mobile Punching", "Verifies exact GPS latitude/longitude and office geofence radius before logging attendance. Eliminates proxy punches and buddy check-ins entirely.", "Fraud Prevention", ACCENT_GREEN)
    add_card(slide4, Inches(0.8), Inches(4.8), Inches(5.6), Inches(2.0), "Instant Encrypted Payslips (PDF)", "Employees access complete compensation history and download password-protected monthly payslips directly to phone storage in seconds.", "Self-Service", ACCENT_BLUE)

    add_card(slide4, Inches(6.9), Inches(2.5), Inches(5.6), Inches(2.0), "Snap & Claim Expense Reimbursements", "Employees snap photos of fuel, meal, and hotel bills while traveling. Receipts attach to live trip logs for instant manager review and approval.", "Zero Paperwork", ACCENT_AMBER)
    add_card(slide4, Inches(6.9), Inches(4.8), Inches(5.6), Inches(2.0), "Real-Time Push Alerts & Notice Board", "Instant push notifications for approved leaves, regularization updates, company announcements, team kudos, and birthday/anniversary celebrations.", "Engagement", ACCENT_PURPLE)

    # ==========================================
    # SLIDE 5: Unique USP - Live Field Travel Desk
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "Market Differentiator", "Live Field Travel & Interactive GPS Map Telemetry", "A native capability unavailable in standard HRMS tools. Eliminates fake expense vouchers permanently.")

    add_card(slide5, Inches(0.8), Inches(2.5), Inches(3.6), Inches(4.2), "Live HR Fleet & Staff Map", "HR and Operations managers monitor live active trips on an interactive satellite map with real-time location pings, route paths, and destination milestones.", "Real-Time Telemetry", ACCENT_BLUE)
    add_card(slide5, Inches(4.8), Inches(2.5), Inches(3.6), Inches(4.2), "Trip-Linked Reimbursements", "Reimbursements are strictly locked to specific official trip IDs. Claims cannot be filed without verified GPS movement, preventing inflated claims.", "Anti-Fraud Control", ACCENT_GREEN)
    add_card(slide5, Inches(8.8), Inches(2.5), Inches(3.6), Inches(4.2), "Branded Trip Dossiers", "Generates comprehensive travel dossiers with trip purpose, boarding passes, client meeting agendas, hotel vouchers, and completed deliverables.", "Executive Reporting", ACCENT_PURPLE)

    # ==========================================
    # SLIDE 6: Performance, OKRs & Monthly Dossier
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "Performance Management", "From Quarterly OKRs to 360 Monthly Review Dossiers", "Objective, data-backed performance reviews that align employee output with company growth.")

    add_card(slide6, Inches(0.8), Inches(2.5), Inches(3.6), Inches(4.2), "Objectives & Key Results (OKRs)", "Employees set quarterly goals with checkable sub-milestones and live progress bars. Managers review progress continuously instead of once a year.", "Goal Alignment", ACCENT_CYAN)
    add_card(slide6, Inches(4.8), Inches(2.5), Inches(3.6), Inches(4.2), "Two-Stage Review Cycles", "Self-appraisal ratings (1 to 5) followed by managerial score and qualitative comments. Ensures fair, transparent, and documented evaluations.", "Structured Review", ACCENT_BLUE)
    add_card(slide6, Inches(8.8), Inches(2.5), Inches(3.6), Inches(4.2), "360 Monthly Review Dossier (PDF)", "A one-click printable A4 dossier pulling attendance rate, leaves, trips, OKRs, and manager feedback onto a single sheet for monthly 1-on-1 meetings.", "1-on-1 Executive Sheet", ACCENT_GREEN)

    # ==========================================
    # SLIDE 7: Compensation Simulator & Increment Letters
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "Compensation Engineering", "Real-Time CTC Simulation & Branded Increment Letters", "Automates salary hike math, promotions, and formal legal documentation seamlessly.")

    add_card(slide7, Inches(0.8), Inches(2.5), Inches(3.6), Inches(4.2), "Real-Time CTC Simulator", "Test hike percentages (10%, 15%) or target CTCs on the fly. The engine recalculates Basic (50%), HRA, PF, Gratuity, Special Allowance, and Net In-Hand automatically.", "Automated Math", ACCENT_AMBER)
    add_card(slide7, Inches(4.8), Inches(2.5), Inches(3.6), Inches(4.2), "1-Click Master Record Sync", "Once HR approves a proposed hike or promotion, the employee's master salary, designation, and tax deductions update across the system immediately.", "Zero Manual Entry", ACCENT_GREEN)
    add_card(slide7, Inches(8.8), Inches(2.5), Inches(3.6), Inches(4.2), "Branded Increment Letters", "Generates formal, print-ready increment and promotion letters on corporate letterhead with full component breakdown tables and executive sign-off blocks.", "Formal Documentation", ACCENT_BLUE)

    # ==========================================
    # SLIDE 8: AI-Powered Workspaces & Screening
    # ==========================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8)
    add_header(slide8, "Artificial Intelligence", "AI HR Policy Chatbot & Automated Resume Screener", "Brings vector search and machine intelligence directly into your HR operations.")

    add_card(slide8, Inches(0.8), Inches(2.5), Inches(5.6), Inches(4.2), "AI HR Policy Assistant (RAG Engine)", "Employees ask natural questions like:\n• 'What is our maternity leave policy?'\n• 'How does local travel reimbursement work?'\n• 'What are the rules for probation confirmation?'\n\nThe AI cites exact handbook clauses with page numbers instantly, eliminating 80% of repetitive HR support queries.", "Vector Knowledge Base", ACCENT_PURPLE)
    add_card(slide8, Inches(6.9), Inches(2.5), Inches(5.6), Inches(4.2), "AI Candidate Resume Screener", "Hiring teams can upload 50+ candidate PDF resumes simultaneously. The AI engine:\n• Extracts work history, skills, and qualifications\n• Scores candidates against the target Job Description (JD)\n• Ranks applicants by match percentage in seconds\n• Generates personalized candidate scrutiny reports", "Recruitment Automation", ACCENT_CYAN)

    # ==========================================
    # SLIDE 9: Security & DPDP Act 2023 Compliance
    # ==========================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9)
    add_header(slide9, "Security & Compliance", "Bank-Grade Privacy: DPDP Act 2023 & Zero Data Sharing", "Your employee records, salary data, and identity proofs are protected by strict legal and technical controls.")

    add_card(slide9, Inches(0.8), Inches(2.5), Inches(2.7), Inches(4.2), "Dedicated Tenant Isolation", "Each company operates in an isolated, partitioned database. Cross-tenant data leakage is architecturally impossible.", "Architecture", ACCENT_BLUE)
    add_card(slide9, Inches(3.8), Inches(2.5), Inches(2.7), Inches(4.2), "AES-256 & TLS 1.3", "Military-grade encryption at rest for databases and documents, with TLS 1.3 encryption across all network transmissions.", "Cryptographic Guard", ACCENT_GREEN)
    add_card(slide9, Inches(6.8), Inches(2.5), Inches(2.7), Inches(4.2), "Strict Non-Sharing Pledge", "We never sell, rent, monetize, or share client data with third parties or data brokers. The client retains 100% data ownership.", "Non-Monetization", ACCENT_CYAN)
    add_card(slide9, Inches(9.8), Inches(2.5), Inches(2.7), Inches(4.2), "Enterprise SaaS Agreement", "Comprehensive Master Subscription Agreement with liability caps, mutual hold-harmless defense, and New Delhi arbitration.", "Legal Shield", ACCENT_AMBER)

    # ==========================================
    # SLIDE 10: Competitor Benchmark Matrix
    # ==========================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10)
    add_header(slide10, "Market Comparison", "How AURA HRMS Compares to Legacy Competitors", "High enterprise functionality without exorbitant multi-year contract traps.")

    table_shape = slide10.shapes.add_table(6, 5, Inches(0.8), Inches(2.3), Inches(11.7), Inches(4.5))
    table = table_shape.table

    cols = ["Core Feature", "AURA HRMS (Our Platform)", "Keka HR", "Darwinbox", "greytHR"]
    for i, name in enumerate(cols):
        cell = table.cell(0, i)
        cell.text = name
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(26, 36, 60)
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = ACCENT_CYAN if i == 1 else TEXT_WHITE

    rows_data = [
        ["Mobile App (iOS & Android)", "Included Free (Full Feature)", "Yes (Base features)", "Yes (Complex)", "Yes (Basic)"],
        ["Live Field GPS Map Telemetry", "Native Built-in Map", "Paid Add-on (High cost)", "Third-party plugin only", "Not Available"],
        ["AI Policy RAG & Resume Screener", "Built-in Core Engine", "Limited Chatbot", "Enterprise Custom Tier", "Not Available"],
        ["Implementation Timeline", "Under 24 Hours", "3 to 6 Weeks", "2 to 4 Months", "2 to 3 Weeks"],
        ["Pricing & Contract Lock-In", "Zero Lock-In (Monthly Billing)", "Min. Rs 60,000+ Annual Lock", "Min. Rs 2,50,000+ Annual Lock", "Min. Rs 35,000+ Annual Lock"]
    ]

    for row_idx, r_data in enumerate(rows_data, start=1):
        for col_idx, text in enumerate(r_data):
            cell = table.cell(row_idx, col_idx)
            cell.text = text
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(16, 23, 40) if col_idx != 1 else RGBColor(24, 38, 70)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(11)
            p.font.color.rgb = ACCENT_GREEN if (col_idx == 1 and row_idx in [1, 2, 3, 4, 5]) else TEXT_MUTED

    # ==========================================
    # SLIDE 11: Measurable Business ROI
    # ==========================================
    slide11 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide11)
    add_header(slide11, "Business Impact", "Measurable Return on Investment Within 30 Days", "Eliminates operational leakages and saves hundreds of administrative management hours.")

    add_card(slide11, Inches(0.8), Inches(2.5), Inches(3.6), Inches(4.2), "85% Payroll Time Saved", "Monthly payroll cycles drop from 4 full days of manual Excel formula reconciliation to under 15 minutes of automated bulk generation.", "Efficiency Gain", ACCENT_GREEN)
    add_card(slide11, Inches(4.8), Inches(2.5), Inches(3.6), Inches(4.2), "100% Elimination of Fake Claims", "GPS verified travel routes and required live camera receipt snaps ensure every reimbursed rupee corresponds to legitimate business travel.", "Fraud Elimination", ACCENT_BLUE)
    add_card(slide11, Inches(8.8), Inches(2.5), Inches(3.6), Inches(4.2), "3.2x Faster Onboarding", "Automated digital document checklists and instant profile setup get new hires productive on Day 1 without endless physical paperwork.", "Productivity Boost", ACCENT_PURPLE)

    # ==========================================
    # SLIDE 12: Fast-Track Implementation
    # ==========================================
    slide12 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide12)
    add_header(slide12, "Rapid Deployment", "Go Live Across Your Organization in 3 Simple Steps", "Zero complicated server installations. Our dedicated deployment team handles everything for you.")

    add_card(slide12, Inches(0.8), Inches(2.5), Inches(3.6), Inches(4.2), "Step 1: Employee Roster Import", "Send us your existing staff Excel or CSV sheet. We map departments, salary structures, leave balances, and shift timings into your dedicated database on Day 1.", "Day 01 Setup", ACCENT_CYAN)
    add_card(slide12, Inches(4.8), Inches(2.5), Inches(3.6), Inches(4.2), "Step 2: Mobile App Rollout", "Employees download the iOS/Android app from app stores, log in with their credentials, and punch in their first geofenced attendance immediately on Day 2.", "Day 02 Activation", ACCENT_GREEN)
    add_card(slide12, Inches(8.8), Inches(2.5), Inches(3.6), Inches(4.2), "Step 3: Run Payroll in 1-Click", "At month end, click 'Generate Bulk Payslips'. Review automated tax, LOP deductions, and approved trip expenses, and distribute digital payslips seamlessly.", "Day 30 Payday", ACCENT_AMBER)

    # ==========================================
    # SLIDE 13: Risk-Free 30-Day Pilot & CTA
    # ==========================================
    slide13 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide13)
    
    # CTA Card
    cta = add_card(slide13, Inches(1.5), Inches(1.5), Inches(10.3), Inches(4.6), "Experience Aura HRMS with a Risk-Free 30-Day Free Pilot", "", "Special Introductory Offer", ACCENT_GREEN)
    tf_cta = cta.text_frame
    
    p_desc = tf_cta.add_paragraph()
    p_desc.text = "Zero upfront setup fees. We configure your company's dedicated workspace, migrate your employee records, and deploy the native mobile app for your entire workforce completely free for 30 days."
    p_desc.font.size = Pt(15)
    p_desc.font.color.rgb = TEXT_MUTED
    p_desc.space_before = Pt(14)
    p_desc.space_after = Pt(20)

    bullets = [
        "Dedicated Account Onboarding Specialist assigned to your team",
        "Full access to Native Mobile Apps (iOS & Android) with live geofenced punch",
        "Complete Indian statutory payroll processing (PF, PT, TDS, LOP)",
        "Zero long-term contract lock-in — continue only if you love the platform"
    ]
    for b in bullets:
        p_b = tf_cta.add_paragraph()
        p_b.text = "   " + b
        p_b.font.size = Pt(13)
        p_b.font.color.rgb = TEXT_WHITE
        p_b.font.bold = True
        p_b.space_after = Pt(8)

    # Save Deck
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Aura_HRMS_Enterprise_Pitch_Deck.pptx")
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_deck()
