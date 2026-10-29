#!/usr/bin/env python3
"""
HRMS Enterprise Pitch Deck - Professional PowerPoint Generator
Color palette extracted from HRMS UI screenshots:
  - Dark Navy:  #0D1B2A (background hero)
  - Deep Blue:  #1A3A5C (sidebar/section bg)
  - Royal Blue: #1D4ED8 (primary accent)
  - Sky Blue:   #3B82F6 (highlights)
  - Cyan:       #06B6D4 (secondary accent)
  - Light Blue: #DBEAFE (cards)
  - White:      #FFFFFF
  - Light Gray: #F8FAFC
  - Dark Text:  #0F172A
  - Muted Text: #64748B
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import pptx.util as util
from pptx.oxml.ns import qn
from lxml import etree
import copy

# ─────────────────────── COLOUR PALETTE ──────────────────────────────────────
C_NAVY       = RGBColor(0x0D, 0x1B, 0x2A)   # dark hero background
C_DEEP_BLUE  = RGBColor(0x1A, 0x3A, 0x5C)   # section accent bg
C_ROYAL      = RGBColor(0x1D, 0x4E, 0xD8)   # primary blue
C_SKY        = RGBColor(0x3B, 0x82, 0xF6)   # highlight blue
C_CYAN       = RGBColor(0x06, 0xB6, 0xD4)   # teal accent
C_GREEN      = RGBColor(0x10, 0xB9, 0x81)   # success green
C_ORANGE     = RGBColor(0xF5, 0x9E, 0x0B)   # warning / highlight
C_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
C_LIGHT_GRAY = RGBColor(0xF8, 0xFA, 0xFC)
C_LIGHT_BLUE = RGBColor(0xDB, 0xEA, 0xFE)
C_DARK_TEXT  = RGBColor(0x0F, 0x17, 0x2A)
C_MUTED      = RGBColor(0x64, 0x74, 0x8B)
C_CARD_BG    = RGBColor(0xEF, 0xF6, 0xFF)

# Slide size: widescreen 16:9
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# Image paths (renamed copies)
IMG_DIR = "/Users/akashd/Documents/PROJECTS/HRMS/IMAGES/hrms_renamed"

def img(n):
    p = os.path.join(IMG_DIR, f"img_{n:02d}.png")
    return p if os.path.exists(p) else None

# ─────────────────────── HELPERS ─────────────────────────────────────────────

def add_rect(slide, x, y, w, h, fill_color, alpha=None):
    shape = slide.shapes.add_shape(1, x, y, w, h)  # MSO_SHAPE_TYPE.RECTANGLE = 1
    shape.line.fill.background()
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    return shape

def add_text_box(slide, text, x, y, w, h,
                 font_size=18, bold=False, color=C_WHITE,
                 align=PP_ALIGN.LEFT, italic=False, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(x, y, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_name
    return txBox

def add_multiline_text(slide, lines, x, y, w, h,
                       font_size=18, bold=False, color=C_WHITE,
                       align=PP_ALIGN.LEFT, font_name="Calibri", spacing=1.2):
    txBox = slide.shapes.add_textbox(x, y, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, (text, fsize, fbold, fcolor) in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(fsize)
        run.font.bold = fbold
        run.font.color.rgb = fcolor
        run.font.name = font_name
    return txBox

def add_image(slide, path, x, y, w, h=None):
    if path and os.path.exists(path):
        try:
            if h:
                pic = slide.shapes.add_picture(path, x, y, w, h)
            else:
                pic = slide.shapes.add_picture(path, x, y, w)
            return pic
        except Exception as e:
            print(f"Warning: could not add image {path}: {e}")
    return None

def add_gradient_rect(slide, x, y, w, h, color1, color2, angle=0):
    """Add a rectangle with a gradient fill (left-to-right or top-to-bottom)."""
    shape = slide.shapes.add_shape(1, x, y, w, h)
    shape.line.fill.background()
    
    # Apply gradient via XML
    sp = shape.element
    spPr = sp.find(qn('p:spPr'))
    
    # Build gradient XML
    gradFill_xml = f'''<a:gradFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" rotWithShape="1">
      <a:gsLst>
        <a:gs pos="0">
          <a:srgbClr val="{color1.rgb}"/>
        </a:gs>
        <a:gs pos="100000">
          <a:srgbClr val="{color2.rgb}"/>
        </a:gs>
      </a:gsLst>
      <a:lin ang="{angle}" scaled="0"/>
    </a:gradFill>'''
    
    # Replace solid fill with gradient
    solidFill = spPr.find(qn('a:solidFill'))
    if solidFill is not None:
        spPr.remove(solidFill)
    
    gradFill = etree.fromstring(gradFill_xml)
    spPr.insert(list(spPr).index(spPr.find(qn('a:ln'))) if spPr.find(qn('a:ln')) is not None else 1, gradFill)
    
    return shape

def set_bg(slide, color):
    """Set solid background color for a slide."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_divider(slide, x, y, w, color=C_SKY, thickness=3):
    """Add a thin horizontal line divider."""
    line = slide.shapes.add_shape(1, x, y, w, Pt(thickness))
    line.fill.solid()
    line.fill.fore_color.rgb = color
    line.line.fill.background()
    return line

def add_badge(slide, text, x, y, w, h, fill_color, text_color=C_WHITE, font_size=11):
    """Add a rounded badge/pill."""
    shape = slide.shapes.add_shape(1, x, y, w, h)
    shape.line.fill.background()
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = True
    run.font.color.rgb = text_color
    run.font.name = "Calibri"
    return shape

def add_feature_card(slide, icon, title, desc, x, y, w=Inches(2.8), h=Inches(1.4)):
    """Add a feature card with icon, title, description."""
    # Card background
    card = slide.shapes.add_shape(1, x, y, w, h)
    card.fill.solid()
    card.fill.fore_color.rgb = C_CARD_BG
    card.line.color.rgb = C_LIGHT_BLUE
    card.line.width = Pt(1)

    # Icon text
    add_text_box(slide, icon, x+Inches(0.12), y+Inches(0.08), Inches(0.4), Inches(0.35),
                 font_size=16, color=C_ROYAL)
    # Title
    add_text_box(slide, title, x+Inches(0.55), y+Inches(0.08), w-Inches(0.65), Inches(0.35),
                 font_size=11, bold=True, color=C_DARK_TEXT)
    # Desc
    add_text_box(slide, desc, x+Inches(0.12), y+Inches(0.5), w-Inches(0.2), Inches(0.75),
                 font_size=9.5, color=C_MUTED)

def add_stat_card(slide, number, label, color, x, y, w=Inches(2.5), h=Inches(1.2)):
    """Add a stat/metric card."""
    card = slide.shapes.add_shape(1, x, y, w, h)
    card.fill.solid()
    card.fill.fore_color.rgb = C_WHITE
    card.line.color.rgb = color
    card.line.width = Pt(3)
    
    # Left accent bar
    bar = slide.shapes.add_shape(1, x, y, Inches(0.07), h)
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    
    # Number
    add_text_box(slide, number, x+Inches(0.15), y+Inches(0.08), w-Inches(0.2), Inches(0.6),
                 font_size=28, bold=True, color=color)
    # Label
    add_text_box(slide, label, x+Inches(0.15), y+Inches(0.68), w-Inches(0.2), Inches(0.4),
                 font_size=10, color=C_MUTED)

# ─────────────────────── SLIDE BUILDERS ──────────────────────────────────────

def build_slide_01_cover(prs):
    """Slide 1: Cover – Hero slide with branding"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    set_bg(slide, C_NAVY)
    
    # Left dark panel
    add_rect(slide, 0, 0, Inches(7.5), SLIDE_H, C_DEEP_BLUE)
    
    # Vertical accent strip
    add_rect(slide, Inches(7.5), 0, Inches(0.06), SLIDE_H, C_SKY)
    
    # Right panel – screenshot
    add_rect(slide, Inches(7.56), 0, Inches(5.77), SLIDE_H, C_NAVY)
    pic = add_image(slide, img(1), Inches(7.6), Inches(0.5), Inches(5.6))
    
    # Tag line badge
    add_badge(slide, "⚡  NEXT-GEN ENTERPRISE HR PLATFORM", Inches(0.5), Inches(1.0),
              Inches(4.5), Inches(0.38), C_ROYAL, C_WHITE, 11)
    
    # Main headline
    add_text_box(slide, "Scale Your Team", Inches(0.5), Inches(1.6), Inches(6.8), Inches(1.0),
                 font_size=44, bold=True, color=C_WHITE)
    add_text_box(slide, "with Precision.", Inches(0.5), Inches(2.5), Inches(6.8), Inches(1.0),
                 font_size=44, bold=True, color=C_SKY)
    
    # Divider
    add_divider(slide, Inches(0.5), Inches(3.55), Inches(5.5), C_CYAN, 3)
    
    # Sub-text
    add_text_box(slide,
                 "A centralized Human Resource Management System built for modern enterprises.\n"
                 "Streamline attendance, payroll, and employee records — all in one secure platform.",
                 Inches(0.5), Inches(3.7), Inches(6.7), Inches(1.5),
                 font_size=14, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    # Stats row
    stats = [("1,200+", "Employees Managed"), ("40+", "Modules"), ("99.9%", "Uptime SLA")]
    for i, (num, label) in enumerate(stats):
        xi = Inches(0.5 + i * 2.2)
        add_text_box(slide, num, xi, Inches(5.4), Inches(2.0), Inches(0.55),
                     font_size=24, bold=True, color=C_CYAN)
        add_text_box(slide, label, xi, Inches(5.9), Inches(2.0), Inches(0.4),
                     font_size=10, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    # Bottom bar
    add_rect(slide, 0, Inches(6.9), SLIDE_W, Inches(0.6), C_ROYAL)
    add_text_box(slide, "HRMS  |  Enterprise Workforce Management  |  Web + Mobile  |  Confidential",
                 Inches(0.5), Inches(6.95), Inches(12.33), Inches(0.4),
                 font_size=10, color=RGBColor(0xDB, 0xEA, 0xFE), align=PP_ALIGN.CENTER)


def build_slide_02_agenda(prs):
    """Slide 2: Agenda / What We'll Cover"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_LIGHT_GRAY)
    
    # Top header band
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.4), C_NAVY)
    add_text_box(slide, "What We'll Cover Today", Inches(0.5), Inches(0.35), Inches(10), Inches(0.8),
                 font_size=30, bold=True, color=C_WHITE)
    add_text_box(slide, "A structured walkthrough of the HRMS platform capabilities and business value",
                 Inches(0.5), Inches(0.9), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "2", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    agenda_items = [
        ("01", "Platform Overview", "The what & why of HRMS – problems solved, architecture, and key differentiators.", C_ROYAL),
        ("02", "Core Web Modules", "HR Commander, Attendance, Payroll, Leave, Expenses, Trips, Documents & more.", C_SKY),
        ("03", "Mobile Application", "Employee Terminal & HR Terminal – the full power of HRMS in your pocket.", C_CYAN),
        ("04", "AI & Automation", "Smart payroll engine, geo-fencing, analytics reports, and AI Workspace.", C_GREEN),
        ("05", "Security & Compliance", "Multi-tenant isolation, role-based access, data privacy, audit trails.", C_ORANGE),
        ("06", "ROI & Why Choose Us", "Cost savings, time-to-value, competitive edge, and deployment roadmap.", C_ROYAL),
    ]
    
    cols = 3
    card_w = Inches(3.9)
    card_h = Inches(1.5)
    start_x = Inches(0.4)
    start_y = Inches(1.6)
    gap_x = Inches(0.25)
    gap_y = Inches(0.2)
    
    for i, (num, title, desc, color) in enumerate(agenda_items):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        
        card = slide.shapes.add_shape(1, x, y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = C_WHITE
        card.line.color.rgb = color
        card.line.width = Pt(2)
        
        # Number badge
        add_rect(slide, x, y, Inches(0.55), card_h, color)
        add_text_box(slide, num, x, y + Inches(0.5), Inches(0.55), Inches(0.55),
                     font_size=16, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        
        add_text_box(slide, title, x+Inches(0.65), y+Inches(0.12), card_w-Inches(0.75), Inches(0.45),
                     font_size=13, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, desc, x+Inches(0.65), y+Inches(0.55), card_w-Inches(0.75), Inches(0.85),
                     font_size=10, color=C_MUTED)
    
    # Bottom bar
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_03_problem(prs):
    """Slide 3: The Problem – Why HR needs to change"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_WHITE)
    
    # Header
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.5), C_NAVY)
    add_text_box(slide, "The HR Challenge", Inches(0.5), Inches(0.25), Inches(9), Inches(0.7),
                 font_size=32, bold=True, color=C_WHITE)
    add_text_box(slide, "Why traditional HR processes are costing your business",
                 Inches(0.5), Inches(0.9), Inches(9), Inches(0.45),
                 font_size=13, color=C_LIGHT_BLUE)
    add_text_box(slide, "3", Inches(12.6), Inches(0.4), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Left: Pain points
    pain_points = [
        ("🕒", "Manual Attendance Tracking", "Paper registers and Excel punch-ins lead to errors, buddy punching, and audit failures."),
        ("💸", "Payroll Errors & Delays", "Manual salary calculations miss TDS, PF, LOP deductions — creating compliance risks."),
        ("📋", "Fragmented HR Systems", "Leave, expenses, trips, and documents managed in separate tools with no unified view."),
        ("📱", "No Mobile Accessibility", "Field employees can't track attendance, request leaves, or submit expenses on the go."),
        ("🔒", "Data Security Gaps", "Sensitive HR data stored in shared drives and unencrypted spreadsheets."),
    ]
    
    for i, (icon, title, desc) in enumerate(pain_points):
        y = Inches(1.7 + i * 1.0)
        add_rect(slide, Inches(0.3), y + Inches(0.1), Inches(0.05), Inches(0.7),
                 RGBColor(0xEF, 0x44, 0x44))
        add_text_box(slide, icon + "  " + title, Inches(0.5), y + Inches(0.05), Inches(6.0), Inches(0.4),
                     font_size=13, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, desc, Inches(0.5), y + Inches(0.42), Inches(6.0), Inches(0.5),
                     font_size=10.5, color=C_MUTED)
    
    # Right: stat visual
    add_rect(slide, Inches(7.0), Inches(1.6), Inches(5.9), Inches(5.6), C_LIGHT_GRAY)
    add_text_box(slide, "Industry Pain Numbers", Inches(7.2), Inches(1.75), Inches(5.5), Inches(0.5),
                 font_size=14, bold=True, color=C_DARK_TEXT)
    
    stats_r = [
        ("37%", "of payroll errors go undetected for >1 month", C_ROYAL),
        ("5.2 hrs", "avg. HR time/week lost on manual attendance", C_ORANGE),
        ("2.4x", "compliance risk without automated audit trails", RGBColor(0xEF, 0x44, 0x44)),
        ("68%", "employees want mobile HR access", C_GREEN),
    ]
    for i, (num, label, color) in enumerate(stats_r):
        yi = Inches(2.4 + i * 1.1)
        add_rect(slide, Inches(7.2), yi, Inches(5.5), Inches(0.9), C_WHITE)
        add_rect(slide, Inches(7.2), yi, Inches(0.07), Inches(0.9), color)
        add_text_box(slide, num, Inches(7.4), yi + Inches(0.05), Inches(1.8), Inches(0.45),
                     font_size=26, bold=True, color=color)
        add_text_box(slide, label, Inches(9.3), yi + Inches(0.2), Inches(3.3), Inches(0.6),
                     font_size=11, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_04_solution(prs):
    """Slide 4: Platform Overview – The HRMS Solution"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_NAVY)
    
    # Header
    add_text_box(slide, "The HRMS Solution", Inches(0.5), Inches(0.3), Inches(9), Inches(0.65),
                 font_size=32, bold=True, color=C_WHITE)
    add_text_box(slide, "One unified platform. Web + Mobile. Real-time. Compliance-ready.",
                 Inches(0.5), Inches(0.9), Inches(9), Inches(0.4),
                 font_size=13, color=C_LIGHT_BLUE)
    add_divider(slide, Inches(0.5), Inches(1.35), Inches(3.0), C_SKY, 3)
    add_text_box(slide, "4", Inches(12.6), Inches(0.3), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Main screenshot on right
    add_image(slide, img(1), Inches(7.2), Inches(1.5), Inches(5.8), Inches(4.5))
    
    # Feature bullets on left
    features = [
        (C_SKY,   "🏢 Web HR Portal",    "Full-featured HR portal for admins, managers & employees"),
        (C_CYAN,  "📱 Native Mobile App","iOS & Android apps for on-the-go HR management"),
        (C_GREEN, "📍 GPS Geofencing",   "Location-verified punch in/out with real-time tracking"),
        (C_ORANGE,"💰 Smart Payroll",    "Auto-compute salary, TDS, PF, LOP with one-click payslips"),
        (C_ROYAL, "📊 Live Analytics",   "Real-time dashboards with workforce insights & reports"),
        (C_CYAN,  "🔐 Multi-Tenant",     "Isolated data per company – enterprise-grade security"),
    ]
    
    for i, (color, title, desc) in enumerate(features):
        y = Inches(1.5 + i * 0.9)
        dot = slide.shapes.add_shape(1, Inches(0.4), y + Inches(0.1), Inches(0.28), Inches(0.28))
        dot.fill.solid()
        dot.fill.fore_color.rgb = color
        dot.line.fill.background()
        
        add_text_box(slide, title, Inches(0.8), y, Inches(6.0), Inches(0.38),
                     font_size=13, bold=True, color=C_WHITE)
        add_text_box(slide, desc, Inches(0.8), y + Inches(0.38), Inches(6.0), Inches(0.4),
                     font_size=10.5, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_ROYAL)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_LIGHT_BLUE, align=PP_ALIGN.CENTER)


def build_slide_05_modules_overview(prs):
    """Slide 5: 8 Core Modules Visual Grid"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_LIGHT_GRAY)
    
    # Header
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.35), C_DEEP_BLUE)
    add_text_box(slide, "8 Powerful Modules. One Platform.", Inches(0.5), Inches(0.25), Inches(10), Inches(0.7),
                 font_size=30, bold=True, color=C_WHITE)
    add_text_box(slide, "Everything your HR team needs — engineered for operational excellence",
                 Inches(0.5), Inches(0.88), Inches(10), Inches(0.38),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "5", Inches(12.6), Inches(0.4), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    modules = [
        ("📍", "GPS Attendance",    "Geofenced punch in/out\nfrom mobile with live tracking",    C_ROYAL),
        ("📅", "Leave Management",  "Apply, approve & track leave\nbalances seamlessly",         C_SKY),
        ("💰", "Payroll & Payslips","Auto-compute salary with\nLOP, PF, TDS deductions",         C_GREEN),
        ("✈️", "Trip Management",   "Request & audit field trips\nwith GPS route tracking",      C_ORANGE),
        ("🧾", "Expense Claims",    "Submit & approve expenses\nwith receipt verification",      C_CYAN),
        ("📄", "Document Vault",    "Upload & manage employee\ndocs, certs & ID cards",          C_ROYAL),
        ("✅", "Department Tasks",  "Assign, track & monitor\nteam tasks & training",            C_SKY),
        ("📢", "Notice Board",      "Company announcements\n& broadcast notifications",          C_GREEN),
    ]
    
    cols = 4
    card_w = Inches(2.95)
    card_h = Inches(2.0)
    start_x = Inches(0.35)
    start_y = Inches(1.5)
    gap_x = Inches(0.25)
    gap_y = Inches(0.22)
    
    for i, (icon, title, desc, color) in enumerate(modules):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        
        card = slide.shapes.add_shape(1, x, y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = C_WHITE
        card.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
        card.line.width = Pt(1)
        
        # Top color strip
        strip = slide.shapes.add_shape(1, x, y, card_w, Inches(0.12))
        strip.fill.solid()
        strip.fill.fore_color.rgb = color
        strip.line.fill.background()
        
        # Icon
        add_text_box(slide, icon, x + Inches(0.15), y + Inches(0.22), Inches(0.5), Inches(0.55),
                     font_size=22, color=color)
        # Title
        add_text_box(slide, title, x + Inches(0.75), y + Inches(0.25), card_w - Inches(0.9), Inches(0.45),
                     font_size=12, bold=True, color=C_DARK_TEXT)
        # Desc
        add_text_box(slide, desc, x + Inches(0.15), y + Inches(0.88), card_w - Inches(0.3), Inches(0.9),
                     font_size=10, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_06_attendance(prs):
    """Slide 6: Attendance & Geofencing"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_WHITE)
    
    # Left accent panel
    add_rect(slide, 0, 0, Inches(0.3), SLIDE_H, C_ROYAL)
    
    # Header
    add_rect(slide, Inches(0.3), 0, SLIDE_W - Inches(0.3), Inches(1.4), C_NAVY)
    add_text_box(slide, "📍  GPS Attendance & Geofencing", Inches(0.6), Inches(0.25), Inches(10), Inches(0.65),
                 font_size=28, bold=True, color=C_WHITE)
    add_text_box(slide, "Real-time, location-verified workforce attendance management",
                 Inches(0.6), Inches(0.88), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "6", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Screenshot: geofence settings
    add_image(slide, img(11), Inches(0.4), Inches(1.55), Inches(7.2), Inches(4.5))
    
    # Right: key points
    points = [
        (C_ROYAL, "3D Geofenced Punch In/Out",
         "Define exact office coordinates with configurable radius.\nEmployees can only punch in when within the allowed zone."),
        (C_SKY, "Live Attendance Dashboard",
         "Real-time view of who is present, on shift, or absent.\nNotification alerts for unverified punches."),
        (C_GREEN, "Missed Punch Regularization",
         "Employees submit regularization requests for missed punches.\nManagers approve/reject with audit trail."),
        (C_ORANGE, "Shift & Roster Management",
         "Configure multiple shift types, roster calendars,\nand automatic shift assignments per department."),
    ]
    
    for i, (color, title, desc) in enumerate(points):
        y = Inches(1.55 + i * 1.4)
        add_rect(slide, Inches(7.8), y, Inches(0.06), Inches(1.1), color)
        add_text_box(slide, title, Inches(8.0), y, Inches(5.0), Inches(0.42),
                     font_size=13, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, desc, Inches(8.0), y + Inches(0.42), Inches(5.0), Inches(0.75),
                     font_size=10.5, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_07_payroll(prs):
    """Slide 7: Smart Payroll & Payslips"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_LIGHT_GRAY)
    
    # Header
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.4), C_DEEP_BLUE)
    add_text_box(slide, "💰  Smart Payroll & Automated Payslips", Inches(0.5), Inches(0.25), Inches(10), Inches(0.65),
                 font_size=28, bold=True, color=C_WHITE)
    add_text_box(slide, "Compliance-first payroll with TDS, PF, and LOP — one-click payslip generation",
                 Inches(0.5), Inches(0.88), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "7", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Left: payroll screenshot
    add_image(slide, img(14), Inches(0.3), Inches(1.55), Inches(5.5), Inches(4.5))
    
    # Right: payslip preview screenshot
    add_image(slide, img(11), Inches(6.0), Inches(1.55), Inches(3.5), Inches(2.8))
    
    # Feature list
    payroll_features = [
        ("✅ Auto-Compute Salary", "LOP, PF, ESI, TDS, Bonus — all calculated automatically"),
        ("✅ Payslip Live Preview", "See formatted payslip in real-time before publishing"),
        ("✅ Bulk Payroll Run", "Process payroll for entire workforce in one click"),
        ("✅ Salary Structure Config", "Customizable CTC breakdown per employee grade"),
    ]
    
    for i, (title, desc) in enumerate(payroll_features):
        y = Inches(4.6 + i * 0.55)
        add_text_box(slide, title, Inches(6.0), y, Inches(7.0), Inches(0.3),
                     font_size=11, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, desc, Inches(6.0), y + Inches(0.3), Inches(7.0), Inches(0.25),
                     font_size=10, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_08_trips(prs):
    """Slide 8: Trip & Field Management"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_WHITE)
    
    add_rect(slide, 0, 0, Inches(0.3), SLIDE_H, C_CYAN)
    add_rect(slide, Inches(0.3), 0, SLIDE_W - Inches(0.3), Inches(1.4), C_NAVY)
    add_text_box(slide, "✈️  Business Trip & Field Route Management", Inches(0.6), Inches(0.25), Inches(10), Inches(0.65),
                 font_size=28, bold=True, color=C_WHITE)
    add_text_box(slide, "Full visibility into field employee movements, GPS routes, and task completion",
                 Inches(0.6), Inches(0.88), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "8", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Trip request screenshot
    add_image(slide, img(23), Inches(0.4), Inches(1.55), Inches(6.8), Inches(4.5))
    
    # Route audit screenshot
    add_image(slide, img(7), Inches(7.3), Inches(1.55), Inches(5.7), Inches(3.0))
    
    # Key features
    trip_points = [
        (C_CYAN, "GPS Route Audit: 621km tracked, 7 waypoints logged per trip"),
        (C_ROYAL, "3D Map Pin: Set exact client/destination coordinates with OpenStreetMap"),
        (C_GREEN, "Daily Work Records: Tasks done, check-in/out timestamps, shift summaries"),
        (C_ORANGE, "Manager Approval Workflow: Requests routed for managerial sign-off"),
    ]
    for i, (color, text) in enumerate(trip_points):
        y = Inches(4.75 + i * 0.48)
        dot = slide.shapes.add_shape(1, Inches(7.3), y + Inches(0.1), Inches(0.2), Inches(0.2))
        dot.fill.solid()
        dot.fill.fore_color.rgb = color
        dot.line.fill.background()
        add_text_box(slide, text, Inches(7.65), y, Inches(5.4), Inches(0.4),
                     font_size=10.5, color=C_DARK_TEXT)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_09_hr_dashboard(prs):
    """Slide 9: HR Commander Dashboard"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_LIGHT_GRAY)
    
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.4), C_NAVY)
    add_text_box(slide, "🖥  HR Commander — Control Center", Inches(0.5), Inches(0.25), Inches(10), Inches(0.65),
                 font_size=28, bold=True, color=C_WHITE)
    add_text_box(slide, "Real-time workforce attendance and operational metrics at a glance",
                 Inches(0.5), Inches(0.88), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "9", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Main dashboard screenshot
    add_image(slide, img(3), Inches(0.3), Inches(1.55), Inches(8.5), Inches(5.3))
    
    # Right sidebar
    dashboard_features = [
        (C_ROYAL, "Live Attendance Feed", "See total present, on shift, and absent employees updated every minute"),
        (C_GREEN, "Notice Board Integration", "Post company-wide announcements directly from the dashboard"),
        (C_SKY, "Analytics & Reports", "Generate attendance, payroll, and leave reports with one click"),
        (C_ORANGE, "Recruitment Pipeline", "Manage job postings, candidate screening, and offer letters"),
        (C_CYAN, "Checklist Pipelines", "Onboarding/offboarding checklists automated per employee"),
    ]
    
    for i, (color, title, desc) in enumerate(dashboard_features):
        y = Inches(1.6 + i * 1.05)
        add_rect(slide, Inches(9.0), y, Inches(0.06), Inches(0.85), color)
        add_text_box(slide, title, Inches(9.2), y, Inches(4.0), Inches(0.38),
                     font_size=12, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, desc, Inches(9.2), y + Inches(0.38), Inches(4.0), Inches(0.5),
                     font_size=10, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_10_mobile_app(prs):
    """Slide 10: Mobile Application Hero"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_NAVY)
    
    # Accent stripe
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), C_SKY)
    
    # Header
    add_text_box(slide, "📱  Mobile Application", Inches(0.5), Inches(0.25), Inches(9), Inches(0.65),
                 font_size=32, bold=True, color=C_WHITE)
    add_text_box(slide, "Full HRMS power in your pocket — iOS & Android native app",
                 Inches(0.5), Inches(0.85), Inches(9), Inches(0.4),
                 font_size=13, color=C_LIGHT_BLUE)
    add_divider(slide, Inches(0.5), Inches(1.3), Inches(4.5), C_CYAN, 3)
    add_text_box(slide, "10", Inches(12.6), Inches(0.3), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Two mobile screenshots side by side
    add_image(slide, img(26), Inches(0.3), Inches(1.5), Inches(3.0), Inches(5.5))   # Employee Terminal
    add_image(slide, img(27), Inches(3.5), Inches(1.5), Inches(3.0), Inches(5.5))   # HR Terminal
    
    # Label the phones
    add_badge(slide, "Employee Terminal", Inches(0.3), Inches(1.2), Inches(3.0), Inches(0.3),
              C_ROYAL, C_WHITE, 10)
    add_badge(slide, "HR Commander Mobile", Inches(3.5), Inches(1.2), Inches(3.0), Inches(0.3),
              C_CYAN, C_DARK_TEXT, 10)
    
    # Right: feature list
    mobile_features = [
        (C_SKY,    "Employee Terminal",       "Mark attendance, view payslips, manage leaves, submit expenses & trips"),
        (C_CYAN,   "HR Commander Mobile",     "Approve leaves, expenses, regularizations & broadcast notices on the go"),
        (C_GREEN,  "GPS-Based Punch",         "Location-aware tap-to-punch with geofence enforcement"),
        (C_ORANGE, "My Trips & Routes",       "Request travel, track GPS waypoints, log task completion"),
        (C_ROYAL,  "Documents & ID Cards",    "View certificates, contract copies and digital employee ID"),
        (C_SKY,    "Helpdesk & Support",      "Raise, track & resolve HR tickets directly from mobile"),
        (C_GREEN,  "Notice Board & Alerts",   "Receive company broadcasts, announcements & push notifications"),
    ]
    
    for i, (color, title, desc) in enumerate(mobile_features):
        y = Inches(1.5 + i * 0.77)
        dot = slide.shapes.add_shape(1, Inches(6.8), y + Inches(0.12), Inches(0.22), Inches(0.22))
        dot.fill.solid()
        dot.fill.fore_color.rgb = color
        dot.line.fill.background()
        add_text_box(slide, title, Inches(7.1), y, Inches(5.9), Inches(0.35),
                     font_size=12, bold=True, color=C_WHITE)
        add_text_box(slide, desc, Inches(7.1), y + Inches(0.35), Inches(5.9), Inches(0.38),
                     font_size=10, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_ROYAL)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_LIGHT_BLUE, align=PP_ALIGN.CENTER)


def build_slide_11_employee_terminal(prs):
    """Slide 11: Employee Terminal Deep-Dive"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_WHITE)
    
    add_rect(slide, 0, 0, Inches(0.3), SLIDE_H, C_SKY)
    add_rect(slide, Inches(0.3), 0, SLIDE_W - Inches(0.3), Inches(1.4), C_DEEP_BLUE)
    add_text_box(slide, "Employee Terminal — Mobile Hub", Inches(0.6), Inches(0.25), Inches(10), Inches(0.65),
                 font_size=28, bold=True, color=C_WHITE)
    add_text_box(slide, "Everything an employee needs, one tap away",
                 Inches(0.6), Inches(0.88), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "11", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Screenshot
    add_image(slide, img(26), Inches(0.4), Inches(1.55), Inches(3.2), Inches(5.5))
    
    # Monthly metrics explanation
    add_text_box(slide, "Monthly Performance Metrics", Inches(3.9), Inches(1.6), Inches(9.0), Inches(0.45),
                 font_size=15, bold=True, color=C_DARK_TEXT)
    
    metric_cards = [
        ("Attendance Rate", "Target 85% compliance", C_ROYAL),
        ("Days Present", "Active duty logged", C_GREEN),
        ("Leaves Taken", "Approved monthly", C_ORANGE),
        ("Working Days", "Scheduled shifts", RGBColor(0x7C, 0x3A, 0xED)),
    ]
    
    for i, (title, sub, color) in enumerate(metric_cards):
        col = i % 2
        row = i // 2
        x = Inches(3.9 + col * 4.6)
        y = Inches(2.15 + row * 1.2)
        card = slide.shapes.add_shape(1, x, y, Inches(4.2), Inches(1.0))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_BG
        card.line.color.rgb = color
        card.line.width = Pt(2)
        add_text_box(slide, title, x + Inches(0.15), y + Inches(0.08), Inches(3.8), Inches(0.38),
                     font_size=12, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, sub, x + Inches(0.15), y + Inches(0.52), Inches(3.8), Inches(0.35),
                     font_size=10, color=C_MUTED)
    
    add_text_box(slide, "Employee Core Hub — Quick Actions", Inches(3.9), Inches(4.65), Inches(9.0), Inches(0.45),
                 font_size=14, bold=True, color=C_DARK_TEXT)
    
    actions = [
        ("Mark Attendance", "GPS punch in/out"),
        ("Regularization", "Missed punch fix"),
        ("My Profile", "Personal & job details"),
        ("My Expenses", "Claims & receipts"),
        ("My Trips", "Travel requests"),
        ("My Documents", "Certs & ID cards"),
        ("Notice Board", "Announcements"),
        ("Leaves Hub", "Absence logs & balance"),
        ("Payslips", "Payroll statements"),
        ("Helpdesk", "Raise & track tickets"),
    ]
    
    for i, (title, sub) in enumerate(actions):
        col = i % 5
        row = i // 5
        x = Inches(3.9 + col * 1.85)
        y = Inches(5.2 + row * 0.85)
        mini = slide.shapes.add_shape(1, x, y, Inches(1.7), Inches(0.75))
        mini.fill.solid()
        mini.fill.fore_color.rgb = C_WHITE
        mini.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
        mini.line.width = Pt(1)
        add_text_box(slide, title, x + Inches(0.08), y + Inches(0.05), Inches(1.55), Inches(0.32),
                     font_size=9.5, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, sub, x + Inches(0.08), y + Inches(0.38), Inches(1.55), Inches(0.3),
                     font_size=8.5, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_12_hr_commander_mobile(prs):
    """Slide 12: HR Commander Mobile"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_LIGHT_GRAY)
    
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.4), C_NAVY)
    add_text_box(slide, "HR Commander — Mobile Management Console", Inches(0.5), Inches(0.25), Inches(11), Inches(0.65),
                 font_size=26, bold=True, color=C_WHITE)
    add_text_box(slide, "Full HR control from anywhere — approve, monitor, broadcast on mobile",
                 Inches(0.5), Inches(0.88), Inches(11), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "12", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Mobile screenshot
    add_image(slide, img(27), Inches(0.3), Inches(1.55), Inches(3.2), Inches(5.5))
    
    # Today's operational metrics explanation
    add_text_box(slide, "Today's Operational Metrics", Inches(3.9), Inches(1.6), Inches(9.0), Inches(0.45),
                 font_size=15, bold=True, color=C_DARK_TEXT)
    
    ops_cards = [
        ("Total Present", "0% Attendance rate", C_ROYAL),
        ("Active Shifts", "0% of present staff", C_ORANGE),
        ("Completed", "0% Checked out", C_GREEN),
        ("Absent", "0% Absence rate", RGBColor(0xEF, 0x44, 0x44)),
    ]
    
    for i, (title, sub, color) in enumerate(ops_cards):
        col = i % 2
        row = i // 2
        x = Inches(3.9 + col * 4.6)
        y = Inches(2.15 + row * 1.15)
        card = slide.shapes.add_shape(1, x, y, Inches(4.2), Inches(0.95))
        card.fill.solid()
        card.fill.fore_color.rgb = C_WHITE
        card.line.color.rgb = color
        card.line.width = Pt(2)
        add_rect(slide, x, y, Inches(0.07), Inches(0.95), color)
        add_text_box(slide, title, x + Inches(0.18), y + Inches(0.06), Inches(3.8), Inches(0.38),
                     font_size=12, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, sub, x + Inches(0.18), y + Inches(0.5), Inches(3.8), Inches(0.35),
                     font_size=10, color=C_MUTED)
    
    add_text_box(slide, "HR Core Operations at Your Fingertips", Inches(3.9), Inches(4.65), Inches(9.0), Inches(0.45),
                 font_size=14, bold=True, color=C_DARK_TEXT)
    
    hr_ops = [
        ("Leave Requests", "Approve time-off"),
        ("Expense Claims", "Verify receipts"),
        ("Regularizations", "Approve missed punches"),
        ("Trip Tracking", "Live transit routes"),
        ("Helpdesk Queue", "Resolve staff tickets"),
        ("Broadcast Center", "Notice board"),
    ]
    
    for i, (title, sub) in enumerate(hr_ops):
        col = i % 3
        row = i // 3
        x = Inches(3.9 + col * 3.1)
        y = Inches(5.2 + row * 0.9)
        card = slide.shapes.add_shape(1, x, y, Inches(2.85), Inches(0.78))
        card.fill.solid()
        card.fill.fore_color.rgb = C_WHITE
        card.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
        card.line.width = Pt(1)
        add_text_box(slide, title, x + Inches(0.1), y + Inches(0.05), Inches(2.6), Inches(0.35),
                     font_size=10.5, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, sub, x + Inches(0.1), y + Inches(0.42), Inches(2.6), Inches(0.28),
                     font_size=9, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_13_security(prs):
    """Slide 13: Security & Compliance"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_NAVY)
    
    add_text_box(slide, "🔐  Enterprise Security & Compliance", Inches(0.5), Inches(0.3), Inches(10), Inches(0.65),
                 font_size=30, bold=True, color=C_WHITE)
    add_text_box(slide, "Built for regulated industries — data privacy, audit trails, role isolation",
                 Inches(0.5), Inches(0.9), Inches(10), Inches(0.4),
                 font_size=13, color=C_LIGHT_BLUE)
    add_divider(slide, Inches(0.5), Inches(1.35), Inches(4.0), C_CYAN, 3)
    add_text_box(slide, "13", Inches(12.6), Inches(0.3), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    security_items = [
        ("🏢", "Multi-Tenant Architecture",
         "Complete data isolation per company. Each tenant's GPS coordinates, payroll rules, and employee records are completely segregated.",
         C_ROYAL),
        ("👥", "Role-Based Access Control",
         "Super Admin → Company Admin → HR Manager → Department Manager → Employee. Granular permission layers.",
         C_SKY),
        ("📍", "Geofence Enforcement",
         "Strict GPS boundary enforcement prevents fraudulent attendance. Configurable radius with live location verification.",
         C_GREEN),
        ("📋", "Full Audit Trails",
         "Every action logged — payroll runs, attendance modifications, document uploads, and approval workflows.",
         C_ORANGE),
        ("🔒", "Data Encryption & Privacy",
         "All sensitive data encrypted at rest and in transit. GDPR-aligned data handling with configurable retention policies.",
         C_CYAN),
        ("⚡", "99.9% Uptime SLA",
         "Cloud-hosted with auto-scaling infrastructure, automated backups, and disaster recovery.",
         C_ROYAL),
    ]
    
    cols = 2
    card_w = Inches(5.9)
    card_h = Inches(1.4)
    start_x = Inches(0.4)
    start_y = Inches(1.6)
    gap_x = Inches(0.5)
    gap_y = Inches(0.2)
    
    for i, (icon, title, desc, color) in enumerate(security_items):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        
        card = slide.shapes.add_shape(1, x, y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = C_DEEP_BLUE
        card.line.color.rgb = color
        card.line.width = Pt(2)
        
        add_text_box(slide, icon, x + Inches(0.15), y + Inches(0.15), Inches(0.55), Inches(0.55),
                     font_size=20, color=color)
        add_text_box(slide, title, x + Inches(0.8), y + Inches(0.12), card_w - Inches(0.9), Inches(0.4),
                     font_size=13, bold=True, color=C_WHITE)
        add_text_box(slide, desc, x + Inches(0.15), y + Inches(0.62), card_w - Inches(0.25), Inches(0.68),
                     font_size=10, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_ROYAL)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_LIGHT_BLUE, align=PP_ALIGN.CENTER)


def build_slide_14_analytics(prs):
    """Slide 14: Analytics & Reporting"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_WHITE)
    
    add_rect(slide, 0, 0, Inches(0.3), SLIDE_H, C_GREEN)
    add_rect(slide, Inches(0.3), 0, SLIDE_W - Inches(0.3), Inches(1.4), C_NAVY)
    add_text_box(slide, "📊  Analytics, Reports & AI Workspace", Inches(0.6), Inches(0.25), Inches(10), Inches(0.65),
                 font_size=28, bold=True, color=C_WHITE)
    add_text_box(slide, "Data-driven HR decisions backed by real-time analytics and AI-powered insights",
                 Inches(0.6), Inches(0.88), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "14", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Analytics screenshot
    add_image(slide, img(3), Inches(0.4), Inches(1.55), Inches(7.0), Inches(5.0))
    
    # Right: analytics features
    analytics_features = [
        (C_ROYAL, "Real-Time Dashboards",
         "Live workforce metrics — presence rate, absent employees, shift status updated every 60 seconds"),
        (C_GREEN, "Comprehensive Reports",
         "Attendance, payroll, leave, expense, and trip reports — exportable to Excel/PDF"),
        (C_SKY, "AI Workspace",
         "Natural language HR queries — ask 'Who was absent last week?' and get instant answers"),
        (C_ORANGE, "Project Timesheets",
         "Track billable hours per project, client, and employee for professional services firms"),
        (C_CYAN, "Roster & Shift Analytics",
         "Visualize shift patterns, roster gaps, and coverage metrics across departments"),
    ]
    
    for i, (color, title, desc) in enumerate(analytics_features):
        y = Inches(1.6 + i * 1.05)
        add_rect(slide, Inches(7.6), y, Inches(0.06), Inches(0.8), color)
        add_text_box(slide, title, Inches(7.8), y, Inches(5.2), Inches(0.38),
                     font_size=12, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, desc, Inches(7.8), y + Inches(0.38), Inches(5.2), Inches(0.5),
                     font_size=10, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_15_roi(prs):
    """Slide 15: ROI & Business Case"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_LIGHT_GRAY)
    
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.4), C_DEEP_BLUE)
    add_text_box(slide, "💹  ROI & Business Value", Inches(0.5), Inches(0.25), Inches(10), Inches(0.65),
                 font_size=30, bold=True, color=C_WHITE)
    add_text_box(slide, "Quantifiable returns from day one of HRMS deployment",
                 Inches(0.5), Inches(0.88), Inches(10), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "15", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # ROI stat cards
    roi_stats = [
        ("85%", "Reduction in\nManual HR Work", C_ROYAL),
        ("40%", "Faster Payroll\nProcessing", C_GREEN),
        ("0", "Compliance\nViolations", C_CYAN),
        ("2x", "Employee\nSelf-Service", C_ORANGE),
    ]
    
    for i, (num, label, color) in enumerate(roi_stats):
        x = Inches(0.4 + i * 3.2)
        card = slide.shapes.add_shape(1, x, Inches(1.6), Inches(2.9), Inches(2.4))
        card.fill.solid()
        card.fill.fore_color.rgb = C_WHITE
        card.line.color.rgb = color
        card.line.width = Pt(3)
        
        # Top strip
        strip = slide.shapes.add_shape(1, x, Inches(1.6), Inches(2.9), Inches(0.12))
        strip.fill.solid()
        strip.fill.fore_color.rgb = color
        strip.line.fill.background()
        
        add_text_box(slide, num, x, Inches(1.85), Inches(2.9), Inches(1.0),
                     font_size=48, bold=True, color=color, align=PP_ALIGN.CENTER)
        add_text_box(slide, label, x, Inches(2.85), Inches(2.9), Inches(0.85),
                     font_size=12, color=C_DARK_TEXT, align=PP_ALIGN.CENTER)
    
    # Detailed benefits table
    benefits = [
        ("Time Savings",      "5.2 hrs/week HR admin time reclaimed per HR manager through automation"),
        ("Cost Reduction",    "60-70% reduction in payroll processing costs with automation"),
        ("Compliance",        "Zero manual errors in statutory deductions (TDS, PF, ESI) with auto-compute"),
        ("Employee Morale",   "Mobile self-service reduces HR dependency for 90% of routine requests"),
        ("Field Visibility",  "100% GPS accountability for field employees — zero ghost attendance"),
        ("Decision Making",   "Real-time analytics enable proactive workforce planning vs reactive management"),
    ]
    
    add_text_box(slide, "Detailed Business Benefits", Inches(0.4), Inches(4.25), Inches(12.5), Inches(0.4),
                 font_size=14, bold=True, color=C_DARK_TEXT)
    
    for i, (category, benefit) in enumerate(benefits):
        col = i % 2
        row = i // 2
        x = Inches(0.4 + col * 6.4)
        y = Inches(4.75 + row * 0.7)
        
        add_rect(slide, x, y + Inches(0.08), Inches(0.18), Inches(0.18), C_ROYAL)
        add_text_box(slide, category + ":", x + Inches(0.28), y, Inches(1.5), Inches(0.35),
                     font_size=11, bold=True, color=C_DARK_TEXT)
        add_text_box(slide, benefit, x + Inches(1.85), y, Inches(4.3), Inches(0.55),
                     font_size=10, color=C_MUTED)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_16_why_us(prs):
    """Slide 16: Why Choose HRMS – Competitive Edge"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_NAVY)
    
    add_text_box(slide, "⭐  Why Choose HRMS?", Inches(0.5), Inches(0.3), Inches(9), Inches(0.65),
                 font_size=32, bold=True, color=C_WHITE)
    add_text_box(slide, "Purpose-built for growing enterprises — not a generic HR tool",
                 Inches(0.5), Inches(0.9), Inches(9), Inches(0.4),
                 font_size=13, color=C_LIGHT_BLUE)
    add_divider(slide, Inches(0.5), Inches(1.35), Inches(4.0), C_CYAN, 3)
    add_text_box(slide, "16", Inches(12.6), Inches(0.3), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    differentiators = [
        ("🌐 + 📱", "Web & Mobile — Unified",
         "Complete feature parity between web portal and mobile app.\nNo compromised mobile experience."),
        ("📍", "GPS-First Design",
         "Not an afterthought — geofencing, trip tracking, and live location\nare core platform primitives."),
        ("🏢", "True Multi-Tenancy",
         "Complete isolation per company — not just user-level filtering.\nYour data is always yours alone."),
        ("🤖", "AI-Powered HR",
         "Natural language workforce queries, AI-assisted payslip generation,\nand intelligent anomaly alerts."),
        ("⚙️", "Fully Configurable",
         "Salary structures, shift types, geofence zones, leave policies —\ncustomized to your exact workflow."),
        ("🚀", "Fast Deployment",
         "Go live in < 2 weeks. Bulk employee import, automated onboarding,\nzero infrastructure setup required."),
    ]
    
    cols = 3
    card_w = Inches(4.0)
    card_h = Inches(1.65)
    start_x = Inches(0.4)
    start_y = Inches(1.6)
    gap_x = Inches(0.25)
    gap_y = Inches(0.2)
    
    for i, (icon, title, desc) in enumerate(differentiators):
        col = i % cols
        row = i // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        
        card = slide.shapes.add_shape(1, x, y, card_w, card_h)
        card.fill.solid()
        card.fill.fore_color.rgb = C_DEEP_BLUE
        card.line.color.rgb = C_SKY
        card.line.width = Pt(1)
        
        add_text_box(slide, icon, x + Inches(0.15), y + Inches(0.12), Inches(0.7), Inches(0.55),
                     font_size=18, color=C_CYAN)
        add_text_box(slide, title, x + Inches(0.9), y + Inches(0.12), card_w - Inches(1.0), Inches(0.42),
                     font_size=12, bold=True, color=C_WHITE)
        add_text_box(slide, desc, x + Inches(0.15), y + Inches(0.7), card_w - Inches(0.25), Inches(0.85),
                     font_size=10, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_ROYAL)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_LIGHT_BLUE, align=PP_ALIGN.CENTER)


def build_slide_17_deployment(prs):
    """Slide 17: Deployment & Onboarding Roadmap"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_WHITE)
    
    add_rect(slide, 0, 0, Inches(0.3), SLIDE_H, C_ORANGE)
    add_rect(slide, Inches(0.3), 0, SLIDE_W - Inches(0.3), Inches(1.4), C_NAVY)
    add_text_box(slide, "🚀  Go-Live Roadmap — 2 Weeks to Production", Inches(0.6), Inches(0.25), Inches(11), Inches(0.65),
                 font_size=26, bold=True, color=C_WHITE)
    add_text_box(slide, "A structured, zero-disruption deployment plan for enterprise onboarding",
                 Inches(0.6), Inches(0.88), Inches(11), Inches(0.4),
                 font_size=12, color=C_LIGHT_BLUE)
    add_text_box(slide, "17", Inches(12.6), Inches(0.35), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)
    
    # Timeline
    phases = [
        ("Week 1\nDay 1-3", "Company Setup", [
            "Company profile & branding configuration",
            "Payroll structure & salary components setup",
            "Geofence coordinates & shift types configured",
        ], C_ROYAL),
        ("Week 1\nDay 4-5", "Employee Onboarding", [
            "Bulk employee import (Excel/CSV upload)",
            "Role & department assignment",
            "Mobile app invite & first login",
        ], C_SKY),
        ("Week 2\nDay 1-3", "Policy Configuration", [
            "Leave policies, approval workflows",
            "Expense claim limits & categories",
            "Trip management & route rules",
        ], C_GREEN),
        ("Week 2\nDay 4-5", "Training & Go-Live", [
            "HR admin & manager training session",
            "Employee mobile app walkthrough",
            "First payroll run & go-live sign-off",
        ], C_ORANGE),
    ]
    
    phase_w = Inches(2.95)
    start_x = Inches(0.4)
    
    # Connector line
    add_rect(slide, Inches(0.4), Inches(2.45), Inches(12.35), Inches(0.04), C_MUTED)
    
    for i, (timeline, title, tasks, color) in enumerate(phases):
        x = start_x + i * (phase_w + Inches(0.25))
        
        # Timeline label
        add_text_box(slide, timeline, x, Inches(1.5), phase_w, Inches(0.75),
                     font_size=11, bold=True, color=color, align=PP_ALIGN.CENTER)
        
        # Dot on line
        dot = slide.shapes.add_shape(9, x + phase_w/2 - Inches(0.15), Inches(2.32), Inches(0.3), Inches(0.3))
        dot.fill.solid()
        dot.fill.fore_color.rgb = color
        dot.line.color.rgb = C_WHITE
        dot.line.width = Pt(2)
        
        # Phase card
        card = slide.shapes.add_shape(1, x, Inches(2.7), phase_w, Inches(3.8))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD_BG
        card.line.color.rgb = color
        card.line.width = Pt(2)
        
        # Top strip
        strip = slide.shapes.add_shape(1, x, Inches(2.7), phase_w, Inches(0.12))
        strip.fill.solid()
        strip.fill.fore_color.rgb = color
        strip.line.fill.background()
        
        add_text_box(slide, title, x + Inches(0.15), Inches(2.88), phase_w - Inches(0.2), Inches(0.42),
                     font_size=13, bold=True, color=C_DARK_TEXT)
        
        for j, task in enumerate(tasks):
            ty = Inches(3.45 + j * 0.9)
            add_rect(slide, x + Inches(0.15), ty + Inches(0.12), Inches(0.15), Inches(0.15), color)
            add_text_box(slide, task, x + Inches(0.4), ty, phase_w - Inches(0.5), Inches(0.75),
                         font_size=10, color=C_DARK_TEXT)
    
    # Support note
    add_rect(slide, Inches(0.4), Inches(6.7), Inches(12.35), Inches(0.3), C_LIGHT_BLUE)
    add_text_box(slide, "✓ Dedicated implementation manager  ✓ 24/7 support during go-live  ✓ Post-launch success reviews",
                 Inches(0.4), Inches(6.72), Inches(12.35), Inches(0.28),
                 font_size=11, bold=True, color=C_ROYAL, align=PP_ALIGN.CENTER)
    
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), C_NAVY)
    add_text_box(slide, "HRMS Enterprise Platform  |  Confidential",
                 0, Inches(7.15), SLIDE_W, Inches(0.3),
                 font_size=9, color=C_MUTED, align=PP_ALIGN.CENTER)


def build_slide_18_cta(prs):
    """Slide 18: Call to Action – Closing Slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, C_NAVY)
    
    # Bold gradient background effect
    add_rect(slide, 0, 0, Inches(6.5), SLIDE_H, C_DEEP_BLUE)
    add_rect(slide, Inches(6.5), 0, Inches(6.83), SLIDE_H, C_NAVY)
    add_rect(slide, Inches(6.5), 0, Inches(0.06), SLIDE_H, C_SKY)
    
    # Left: CTA
    add_text_box(slide, "Ready to Transform\nYour HR Operations?", Inches(0.5), Inches(1.0), Inches(5.8), Inches(2.2),
                 font_size=34, bold=True, color=C_WHITE)
    
    add_text_box(slide, "Join the enterprises that trust HRMS\nfor their most critical workforce operations.",
                 Inches(0.5), Inches(3.3), Inches(5.8), Inches(1.2),
                 font_size=14, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    # Action buttons
    btn1 = slide.shapes.add_shape(1, Inches(0.5), Inches(4.7), Inches(2.5), Inches(0.6))
    btn1.fill.solid()
    btn1.fill.fore_color.rgb = C_ROYAL
    btn1.line.fill.background()
    tf = btn1.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "Request a Demo"
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = C_WHITE
    run.font.name = "Calibri"
    
    btn2 = slide.shapes.add_shape(1, Inches(3.2), Inches(4.7), Inches(2.5), Inches(0.6))
    btn2.fill.solid()
    btn2.fill.fore_color.rgb = C_DEEP_BLUE
    btn2.line.color.rgb = C_SKY
    btn2.line.width = Pt(2)
    tf2 = btn2.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    run2 = p2.add_run()
    run2.text = "View Live Platform"
    run2.font.size = Pt(13)
    run2.font.bold = True
    run2.font.color.rgb = C_SKY
    run2.font.name = "Calibri"
    
    # Contact details
    add_divider(slide, Inches(0.5), Inches(5.6), Inches(5.5), C_MUTED, 1)
    add_text_box(slide, "📧  hello@hrms-enterprise.com", Inches(0.5), Inches(5.75), Inches(5.5), Inches(0.4),
                 font_size=12, color=RGBColor(0xB0, 0xC4, 0xDE))
    add_text_box(slide, "🌐  www.hrms-enterprise.com", Inches(0.5), Inches(6.15), Inches(5.5), Inches(0.4),
                 font_size=12, color=RGBColor(0xB0, 0xC4, 0xDE))
    add_text_box(slide, "📱  Available on iOS & Android", Inches(0.5), Inches(6.55), Inches(5.5), Inches(0.4),
                 font_size=12, color=RGBColor(0xB0, 0xC4, 0xDE))
    
    # Right: screenshot collage
    add_image(slide, img(26), Inches(6.7), Inches(0.3), Inches(3.0), Inches(5.5))
    add_image(slide, img(3), Inches(9.8), Inches(1.0), Inches(3.2), Inches(4.0))
    
    # HRMS badge
    add_badge(slide, "⚡  HRMS  Enterprise Workforce Platform", Inches(0.5), Inches(0.4),
              Inches(5.5), Inches(0.45), C_ROYAL, C_WHITE, 12)
    
    add_text_box(slide, "18", Inches(12.6), Inches(0.3), Inches(0.6), Inches(0.6),
                 font_size=18, bold=True, color=C_MUTED, align=PP_ALIGN.CENTER)


# ─────────────────────── MAIN ────────────────────────────────────────────────

def build_presentation():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    
    print("Building HRMS Enterprise Pitch Deck...")
    
    build_slide_01_cover(prs)
    print("  ✓ Slide 01: Cover")
    
    build_slide_02_agenda(prs)
    print("  ✓ Slide 02: Agenda")
    
    build_slide_03_problem(prs)
    print("  ✓ Slide 03: The Problem")
    
    build_slide_04_solution(prs)
    print("  ✓ Slide 04: The Solution")
    
    build_slide_05_modules_overview(prs)
    print("  ✓ Slide 05: 8 Modules")
    
    build_slide_06_attendance(prs)
    print("  ✓ Slide 06: Attendance & Geofencing")
    
    build_slide_07_payroll(prs)
    print("  ✓ Slide 07: Payroll & Payslips")
    
    build_slide_08_trips(prs)
    print("  ✓ Slide 08: Trip Management")
    
    build_slide_09_hr_dashboard(prs)
    print("  ✓ Slide 09: HR Commander Dashboard")
    
    build_slide_10_mobile_app(prs)
    print("  ✓ Slide 10: Mobile App Hero")
    
    build_slide_11_employee_terminal(prs)
    print("  ✓ Slide 11: Employee Terminal")
    
    build_slide_12_hr_commander_mobile(prs)
    print("  ✓ Slide 12: HR Commander Mobile")
    
    build_slide_13_security(prs)
    print("  ✓ Slide 13: Security & Compliance")
    
    build_slide_14_analytics(prs)
    print("  ✓ Slide 14: Analytics & Reports")
    
    build_slide_15_roi(prs)
    print("  ✓ Slide 15: ROI & Business Case")
    
    build_slide_16_why_us(prs)
    print("  ✓ Slide 16: Why Choose HRMS")
    
    build_slide_17_deployment(prs)
    print("  ✓ Slide 17: Deployment Roadmap")
    
    build_slide_18_cta(prs)
    print("  ✓ Slide 18: Call to Action")
    
    out_path = "/Users/akashd/Documents/PROJECTS/HRMS/HRMS_Professional_Pitch_Deck_2026.pptx"
    prs.save(out_path)
    print(f"\n✅ Presentation saved: {out_path}")
    print(f"   Total slides: {len(prs.slides)}")
    return out_path


if __name__ == "__main__":
    build_presentation()
