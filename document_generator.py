"""
document_generator.py – Aerospace inspection document generation.

Generates professional PDFs for:
  - Non-Conformance Reports (NCR)
  - Work Orders (WO)
  - Engineering Orders (EO)

Uses reportlab for PDF generation.
"""

import os
import uuid
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

# Output directory for generated documents
DOCS_DIR = os.path.join(os.path.dirname(__file__), "generated_docs")
os.makedirs(DOCS_DIR, exist_ok=True)

# Colour palette
_DARK_BLUE = colors.HexColor("#1a3a5c")
_MID_BLUE  = colors.HexColor("#2c6fad")
_LIGHT_GREY = colors.HexColor("#f0f4f8")
_RED        = colors.HexColor("#dc3545")
_GREEN      = colors.HexColor("#28a745")
_ORANGE     = colors.HexColor("#fd7e14")

DECISION_COLOURS = {
    "ACCEPT":  _GREEN,
    "MONITOR": _ORANGE,
    "REJECT":  _RED,
}


def _doc_number(prefix: str) -> str:
    return f"{prefix}-{date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"


def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="FieldLabel",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="FieldValue",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=_DARK_BLUE,
        spaceBefore=12,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#aaaaaa"),
        spaceAfter=0,
    ))
    return styles


def _header_table(doc_type: str, doc_number: str, styles) -> Table:
    """Blue header banner with document type and number."""
    title_para = Paragraph(doc_type, styles["DocTitle"])
    sub_para   = Paragraph(f"Document No: {doc_number} &nbsp;&nbsp;|&nbsp;&nbsp; Date: {date.today().isoformat()}",
                            styles["DocSubtitle"])
    data = [[title_para], [sub_para]]
    t = Table(data, colWidths=[7 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _DARK_BLUE),
        ("BACKGROUND", (0, 1), (-1, 1), _MID_BLUE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING",   (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 4),
        ("TOPPADDING",   (0, 1), (-1, 1), 6),
        ("BOTTOMPADDING",(0, 1), (-1, 1), 10),
    ]))
    return t


def _field_row(label: str, value: str, styles) -> list:
    """Two-cell row: label above value."""
    return [
        Paragraph(label, styles["FieldLabel"]),
        Paragraph(str(value), styles["FieldValue"]),
    ]


def _two_col_table(rows: list, styles) -> Table:
    """A labelled two-column data table."""
    table_data = []
    for label, value in rows:
        table_data.append([
            Paragraph(label, styles["FieldLabel"]),
            Paragraph(str(value), styles["FieldValue"]),
        ])
    t = Table(table_data, colWidths=[2.2 * inch, 4.8 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), _LIGHT_GREY),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.white, _LIGHT_GREY]),
    ]))
    return t


def _signature_table(blocks: list) -> Table:
    """Signature block row: each block is (title, name_placeholder)."""
    headers = [b[0] for b in blocks]
    lines   = ["_" * 28 for _ in blocks]
    names   = [b[1] for b in blocks]
    t = Table([headers, lines, names],
              colWidths=[7 * inch / len(blocks)] * len(blocks))
    t.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, 0), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), _DARK_BLUE),
        ("FONTSIZE",  (0, 1), (-1, 2), 8),
        ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#888888")),
        ("ALIGN",     (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",(0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_ncr(
    defect_type: str,
    decision: str,
    density: float,
    confidence: float,
    part_number: str = "PN-UNKNOWN",
    zone: str = "UNSPECIFIED",
) -> str:
    """Generate a Non-Conformance Report PDF.

    Parameters
    ----------
    defect_type  : Detected defect classification (scratch / pitting / etc.)
    decision     : Engineering decision (ACCEPT / MONITOR / REJECT)
    density      : Edge-pixel density from inspection
    confidence   : Classifier confidence (0–1)
    part_number  : Aircraft part number
    zone         : Aircraft zone / station identifier

    Returns
    -------
    str – Absolute path to the saved PDF.
    """
    ncr_number = _doc_number("NCR")
    out_path = os.path.join(DOCS_DIR, f"{ncr_number}.pdf")

    doc = SimpleDocTemplate(
        out_path, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = _base_styles()
    story  = []

    # Header
    story.append(_header_table("NON-CONFORMANCE REPORT", ncr_number, styles))
    story.append(Spacer(1, 0.2 * inch))

    # Decision badge
    dec_colour = DECISION_COLOURS.get(decision.upper(), colors.grey)
    badge_style = ParagraphStyle(
        "Badge", fontSize=14, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=1,
    )
    badge_data = [[Paragraph(f"ENGINEERING DECISION: {decision.upper()}", badge_style)]]
    badge_table = Table(badge_data, colWidths=[7 * inch])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), dec_colour),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 0.15 * inch))

    # Identification fields
    story.append(Paragraph("1. IDENTIFICATION", styles["SectionHeader"]))
    story.append(_two_col_table([
        ("NCR Number",    ncr_number),
        ("Date Issued",   date.today().isoformat()),
        ("Part Number",   part_number),
        ("Aircraft Zone", zone),
    ], styles))
    story.append(Spacer(1, 0.1 * inch))

    # Defect details
    story.append(Paragraph("2. DEFECT DETAILS", styles["SectionHeader"]))
    story.append(_two_col_table([
        ("Defect Type",        defect_type.upper()),
        ("Description",        _defect_description(defect_type)),
        ("Edge Density",       f"{density:.4f}"),
        ("Classifier Confidence", f"{confidence:.1%}"),
    ], styles))
    story.append(Spacer(1, 0.1 * inch))

    # Disposition
    story.append(Paragraph("3. DISPOSITION", styles["SectionHeader"]))
    story.append(_two_col_table([
        ("Decision",       decision.upper()),
        ("FAA Reference",  _faa_ref(defect_type)),
        ("Basis",          _decision_basis(decision)),
    ], styles))
    story.append(Spacer(1, 0.2 * inch))

    # Signature block
    story.append(HRFlowable(width="100%", thickness=1, color=_MID_BLUE))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("4. SIGN-OFF", styles["SectionHeader"]))
    story.append(_signature_table([
        ("Inspector / A&P", "Name / Certificate No."),
        ("QA Representative", "Name / Stamp"),
        ("Authorised Inspector", "IA Certificate No."),
    ]))

    doc.build(story)
    return out_path


def generate_work_order(
    defect_type: str,
    decision: str,
    repair_procedure: str,
    part_number: str = "PN-UNKNOWN",
) -> str:
    """Generate a Work Order PDF.

    Parameters
    ----------
    defect_type       : Detected defect classification
    decision          : Engineering disposition (ACCEPT / MONITOR / REJECT)
    repair_procedure  : Repair instructions from the engineering advisory
    part_number       : Aircraft part number

    Returns
    -------
    str – Absolute path to the saved PDF.
    """
    wo_number = _doc_number("WO")
    out_path  = os.path.join(DOCS_DIR, f"{wo_number}.pdf")

    priority     = _wo_priority(decision)
    est_hours    = _wo_hours(decision, defect_type)
    tools        = _wo_tools(defect_type)

    doc = SimpleDocTemplate(
        out_path, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = _base_styles()
    story  = []

    story.append(_header_table("WORK ORDER", wo_number, styles))
    story.append(Spacer(1, 0.2 * inch))

    # Priority badge
    pri_colour = {
        "AOG":       _RED,
        "Routine":   _MID_BLUE,
        "Scheduled": _GREEN,
    }.get(priority, _MID_BLUE)
    pri_style = ParagraphStyle(
        "PriBadge", fontSize=13, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=1,
    )
    pri_table = Table(
        [[Paragraph(f"PRIORITY: {priority}", pri_style)]],
        colWidths=[7 * inch],
    )
    pri_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), pri_colour),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(pri_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("1. WORK ORDER DETAILS", styles["SectionHeader"]))
    story.append(_two_col_table([
        ("WO Number",        wo_number),
        ("Date Issued",      date.today().isoformat()),
        ("Part Number",      part_number),
        ("Defect Type",      defect_type.upper()),
        ("Priority",         priority),
        ("Estimated Hours",  est_hours),
    ], styles))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("2. TASK DESCRIPTION", styles["SectionHeader"]))
    task_style = ParagraphStyle(
        "TaskDesc", parent=styles["Normal"],
        fontSize=9, leading=14, leftIndent=8,
    )
    story.append(Paragraph(repair_procedure, task_style))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("3. REQUIRED TOOLS & MATERIALS", styles["SectionHeader"]))
    tools_style = ParagraphStyle(
        "Tools", parent=styles["Normal"],
        fontSize=9, leading=14, leftIndent=8,
    )
    for tool in tools:
        story.append(Paragraph(f"&#x2022; &nbsp; {tool}", tools_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(HRFlowable(width="100%", thickness=1, color=_MID_BLUE))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("4. SIGN-OFF BLOCKS", styles["SectionHeader"]))
    story.append(_signature_table([
        ("Technician", "Name / Cert."),
        ("Inspector",  "Name / Cert."),
        ("Supervisor", "Name / Date"),
    ]))
    story.append(Spacer(1, 0.15 * inch))

    # Parts / consumables tracking table
    story.append(Paragraph("5. PARTS / CONSUMABLES USED", styles["SectionHeader"]))
    parts_data = [
        ["Part No.", "Description", "Qty", "Batch No.", "Technician"],
        ["", "", "", "", ""],
        ["", "", "", "", ""],
        ["", "", "", "", ""],
    ]
    parts_table = Table(
        parts_data,
        colWidths=[1.2*inch, 2.4*inch, 0.6*inch, 1.2*inch, 1.6*inch],
    )
    parts_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), _DARK_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWHEIGHT",     (0, 1), (-1, -1), 22),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(parts_table)

    doc.build(story)
    return out_path


def generate_engineering_order(
    defect_type: str,
    decision: str,
    regulatory_ref: str = "",
) -> str:
    """Generate an Engineering Order PDF.

    Parameters
    ----------
    defect_type     : Detected defect classification
    decision        : Engineering decision (ACCEPT / MONITOR / REJECT)
    regulatory_ref  : FAA / regulatory reference string

    Returns
    -------
    str – Absolute path to the saved PDF.
    """
    eo_number = _doc_number("EO")
    out_path  = os.path.join(DOCS_DIR, f"{eo_number}.pdf")

    if not regulatory_ref:
        regulatory_ref = _faa_ref(defect_type)

    classification = _eo_classification(decision)
    repair_method  = _eo_repair_method(defect_type, decision)
    tech_desc      = _eo_tech_description(defect_type, decision)

    doc = SimpleDocTemplate(
        out_path, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = _base_styles()
    story  = []

    story.append(_header_table("ENGINEERING ORDER", eo_number, styles))
    story.append(Spacer(1, 0.2 * inch))

    # Classification badge
    cls_colour = {
        "MANDATORY": _RED,
        "CONDITIONAL": _ORANGE,
        "OPTIONAL":    _GREEN,
    }.get(classification, _MID_BLUE)
    cls_style = ParagraphStyle(
        "ClsBadge", fontSize=13, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=1,
    )
    cls_table = Table(
        [[Paragraph(f"CLASSIFICATION: {classification}", cls_style)]],
        colWidths=[7 * inch],
    )
    cls_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), cls_colour),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(cls_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("1. ENGINEERING ORDER DETAILS", styles["SectionHeader"]))
    story.append(_two_col_table([
        ("EO Number",       eo_number),
        ("Date Issued",     date.today().isoformat()),
        ("Defect Type",     defect_type.upper()),
        ("Decision",        decision.upper()),
        ("Classification",  classification),
        ("Regulatory Basis",regulatory_ref),
    ], styles))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("2. TECHNICAL DESCRIPTION", styles["SectionHeader"]))
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=9, leading=14, leftIndent=8,
    )
    story.append(Paragraph(tech_desc, body_style))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("3. REPAIR METHOD", styles["SectionHeader"]))
    story.append(Paragraph(repair_method, body_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(HRFlowable(width="100%", thickness=1, color=_MID_BLUE))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("4. ENGINEERING APPROVAL", styles["SectionHeader"]))
    story.append(_signature_table([
        ("Design Engineer",     "Name / Reg. No."),
        ("DER / DAR",           "Cert. No. / Date"),
        ("Quality Assurance",   "Stamp / Date"),
        ("Approving Authority", "Signature / Date"),
    ]))

    doc.build(story)
    return out_path


# ---------------------------------------------------------------------------
# Private helpers – lookup tables
# ---------------------------------------------------------------------------

def _defect_description(defect_type: str) -> str:
    return {
        "scratch":             "Linear surface damage caused by abrasive contact",
        "pitting":             "Localised corrosion pits on metal surface",
        "crazing":             "Network of fine surface cracks (stress or solvent crazing)",
        "inclusion":           "Foreign material embedded in surface or substrate",
        "clean":               "No significant surface defects detected",
        "unclassified_defect": "Surface anomaly detected; classifier confidence below threshold — manual inspection required",
    }.get(defect_type.lower(), "Unclassified surface anomaly")


def _faa_ref(defect_type: str) -> str:
    return {
        "scratch":             "AC 43.13-1B Chapter 4, Section 4-47",
        "pitting":             "AC 43.13-1B Chapter 6, Section 6-7",
        "crazing":             "AC 43.13-1B Chapter 3, Section 3-6; Chapter 5, Section 5-4",
        "inclusion":           "AC 43.13-1B Chapter 4, Section 4-12; AMS 2631",
        "clean":               "N/A",
        "unclassified_defect": "AC 43.13-1B – consult DER (low-confidence detection)",
    }.get(defect_type.lower(), "AC 43.13-1B – consult DER")


def _decision_basis(decision: str) -> str:
    return {
        "ACCEPT":  "Defect within allowable limits per engineering standard",
        "MONITOR": "Defect approaching limits; schedule follow-up inspection",
        "REJECT":  "Defect exceeds allowable limits; part must be repaired or replaced",
    }.get(decision.upper(), "Engineering judgement required")


def _wo_priority(decision: str) -> str:
    """Map engineering decision to work order priority.

    ACCEPT  → Routine   (no urgency; normal maintenance queue)
    MONITOR → Priority  (schedule within next maintenance window)
    REJECT  → AOG       (Aircraft On Ground; immediate action required)
    """
    return {
        "ACCEPT":  "Routine",
        "MONITOR": "Priority",
        "REJECT":  "AOG",
    }.get(decision.upper(), "Routine")


def _wo_hours(decision: str, defect_type: str) -> str:
    """Estimate labour hours based on engineering decision and defect type."""
    hours = {
        ("ACCEPT",  "scratch"):             "0.5–1 hr (blend/polish)",
        ("ACCEPT",  "pitting"):             "1–2 hrs (chemical treatment)",
        ("ACCEPT",  "crazing"):             "1–2 hrs (surface treatment)",
        ("ACCEPT",  "inclusion"):           "1–2 hrs (documentation + FP inspection)",
        ("ACCEPT",  "clean"):               "0.5 hrs (documentation only)",
        ("MONITOR", "scratch"):             "2–3 hrs (profilometer + blend)",
        ("MONITOR", "pitting"):             "2–4 hrs (chemical treatment + depth measurement)",
        ("MONITOR", "crazing"):             "3–5 hrs (dye-penetrant + repair)",
        ("MONITOR", "inclusion"):           "3–5 hrs (phased-array scan)",
        ("REJECT",  "scratch"):             "4–6 hrs (material removal + DER sign-off)",
        ("REJECT",  "pitting"):             "4–6 hrs (section removal + corrosion treatment)",
        ("REJECT",  "crazing"):             "6–10 hrs (C-scan + composite repair + IA sign-off)",
        ("REJECT",  "inclusion"):           "6–10 hrs (NDE + metallurgical analysis + replacement)",
        ("REJECT",  "unclassified_defect"): "TBD (pending manual inspection and DER review)",
    }
    return hours.get((decision.upper(), defect_type.lower()), "TBD")


def _wo_tools(defect_type: str) -> list:
    base = ["Personal Protective Equipment (PPE)", "Inspection mirror / borescope",
            "Calibrated torque wrench", "Digital profilometer"]
    extras = {
        "inclusion": ["Ultrasonic phased-array scanner (AMS 2631)",
                      "Magnetic particle inspection kit", "Metallurgical sampling tools"],
        "crazing":   ["Dye-penetrant inspection kit (ASTM E1417)",
                      "320-grit abrasive paper", "Two-part polyurethane topcoat",
                      "Fibre-reinforced filler compound"],
        "scratch":   ["400-grit wet/dry abrasive paper", "Blend tool",
                      "Corrosion inhibitor MIL-C-16173 Grade 2"],
        "pitting":   ["Alodine 1200 conversion coating kit",
                      "Phosphoric acid wash solution",
                      "Epoxy primer MIL-PRF-23377", "Pit depth gauge"],
        "clean":               [],
        "unclassified_defect": ["Full visual inspection kit", "Dye-penetrant inspection kit (ASTM E1417)",
                                "Ultrasonic thickness gauge"],
    }
    return base + extras.get(defect_type.lower(), [])


def _eo_classification(decision: str) -> str:
    return {
        "REJECT":  "MANDATORY",
        "MONITOR": "CONDITIONAL",
        "ACCEPT":  "OPTIONAL",
    }.get(decision.upper(), "CONDITIONAL")


def _eo_tech_description(defect_type: str, decision: str) -> str:
    base = _defect_description(defect_type)
    basis = _decision_basis(decision)
    return (
        f"{base}. Automated surface inspection using Canny edge detection and "
        f"density-based classification has determined a {decision.upper()} disposition. "
        f"{basis}. This Engineering Order documents the required technical action and "
        f"serves as the authority for maintenance work under FAA AC 43.13-1B."
    )


def _eo_repair_method(defect_type: str, decision: str) -> str:
    methods = {
        ("scratch",   "ACCEPT"):  "Polish with 400-grit paper; apply MIL-C-16173 corrosion inhibitor; return to service.",
        ("scratch",   "MONITOR"): "Measure depth with profilometer; if < 10% wall thickness, blend and re-inspect in 100 FH.",
        ("scratch",   "REJECT"):  "Material removal blending per AC 43.13-1B Fig. 4-28 or part replacement; DER sign-off required.",
        ("pitting",   "ACCEPT"):  "Alodine 1200 treatment; epoxy primer MIL-PRF-23377 within 4 hours; return to service.",
        ("pitting",   "MONITOR"): "Phosphoric acid wash; pit depth measurement; re-inspect every 50 FH.",
        ("pitting",   "REJECT"):  "Remove affected section; inspect adjacent structure; replace or blend per AC 43.13-1B 6-7(g).",
        ("crazing",   "ACCEPT"):  "Sand with 320-grit; dye-penetrant per ASTM E1417; apply two-part polyurethane topcoat.",
        ("crazing",   "MONITOR"): "Mandatory dye-penetrant; if < 0.005 in. deep, sand, apply filler, re-inspect in 25 FH.",
        ("crazing",   "REJECT"):  "Ground aircraft; ultrasonic C-scan per ASTM E2533; replace/repair per AC 43.13-1B 3-6; IA sign-off.",
        ("inclusion", "ACCEPT"):  "Document location; MP or FP inspection every 200 FH per AMS 2641.",
        ("inclusion", "MONITOR"): "Phased-array ultrasonic per AMS 2631; if < 0.050 in., monitor at 100 FH.",
        ("inclusion", "REJECT"):  "Remove from service; metallurgical analysis per ASTM E2332; replace with AMS 2175 certified material.",
        ("clean",               "ACCEPT"):  "No repair required. Continue normal inspection intervals.",
        ("unclassified_defect", "REJECT"):  "Ground aircraft. Perform full manual visual and NDT inspection. Do not return to service until defect is positively identified and dispositioned by a DER.",
    }
    key = (defect_type.lower(), decision.upper())
    return methods.get(key, "Consult Designated Engineering Representative (DER) for approved repair data.")
