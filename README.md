---
title: Aero Quality Inspector
emoji: ✈️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# Aero Quality Inspector

Automated aerospace surface defect inspection system that classifies surface
anomalies in component images and generates FAA-compliant engineering work
documents — ready for review by an A&P mechanic or DER.

---

## Problem Statement

Manual visual inspection of aerospace components is time-intensive, subjective,
and error-prone. Inspectors must evaluate surface conditions against FAA
Advisory Circular AC 43.13-1B, determine a disposition (accept / monitor /
reject), and produce three separate compliance documents — all under production
pressure.

This system automates the full workflow: upload an image, receive a calibrated
engineering decision grounded in published standards, and download audit-ready
PDFs within seconds.

---

## Pipeline

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│   1 · INSPECT       │     │   2 · ADVISE          │     │   3 · DOCUMENT       │
│                     │     │                       │     │                      │
│  Canny edge         │────▶│  Load AC 43.13-1B     │────▶│  Generate PDFs       │
│  detection on       │     │  thresholds from      │     │                      │
│  input image        │     │  engineering_         │     │  • Non-Conformance   │
│                     │     │  standards.json       │     │    Report  (NCR)     │
│  Classify by        │     │                       │     │  • Work Order  (WO)  │
│  edge density:      │     │  Decision:            │     │  • Engineering       │
│  scratch / pitting  │     │  ACCEPT / MONITOR /   │     │    Order   (EO)      │
│  crazing / inclusion│     │  REJECT               │     │                      │
│                     │     │  + repair procedure   │     │  Signed by A&P / IA  │
└─────────────────────┘     └──────────────────────┘     └──────────────────────┘
         inspector.py               advisor.py                document_generator.py
```

---

## Defect Classification

The inspector uses Canny edge detection and maps edge-pixel density to a defect
class. Each class has a confidence score; detections below 70 % confidence are
flagged as `unclassified_defect` and automatically trigger a REJECT disposition.

| Defect | Edge Density | Description |
|---|---|---|
| clean | < 0.005 | No significant surface anomaly |
| pitting | 0.005 – 0.02 | Localised corrosion pits |
| scratch | 0.02 – 0.05 | Linear abrasive surface damage |
| crazing | 0.05 – 0.15 | Network of fine surface cracks |
| inclusion | > 0.15 | Foreign material embedded in substrate |

Engineering decisions are evaluated against FAA AC 43.13-1B density thresholds
stored in `engineering_standards.json`:

| Defect | ACCEPT ≤ | MONITOR ≤ | REJECT > |
|---|---|---|---|
| scratch | 0.025 | 0.040 | 0.040 |
| pitting | 0.010 | 0.018 | 0.018 |
| crazing | 0.060 | 0.110 | 0.110 |
| inclusion | 0.160 | 0.220 | 0.220 |

---

## File Architecture

| File | Role |
|---|---|
| `app.py` | Entry point — Gradio dashboard, orchestrates the full pipeline |
| `inspector.py` | Canny edge detection, density-based defect classification |
| `advisor.py` | Loads engineering standards, returns ACCEPT / MONITOR / REJECT |
| `document_generator.py` | Generates NCR, Work Order, and Engineering Order PDFs |
| `engineering_standards.json` | FAA AC 43.13-1B thresholds and repair procedures per defect type |
| `requirements.txt` | Python dependencies |
| `report.txt` | Sample inspection output (do not edit manually) |

---

## Generated Documents

Each inspection run produces three downloadable PDFs:

**Non-Conformance Report (NCR)** — Formal record of the detected anomaly.
Includes part number, aircraft zone, edge density, classifier confidence,
engineering decision badge, FAA regulatory basis, and three sign-off blocks
(Inspector / QA Representative / Authorised Inspector).

**Work Order (WO)** — Maintenance task sheet. Includes priority level
(AOG / Routine / Scheduled), estimated labour hours, step-by-step repair
procedure drawn from AC 43.13-1B, required tools and materials checklist,
and a parts/consumables tracking table.

**Engineering Order (EO)** — Technical authority document. Includes an
MANDATORY / CONDITIONAL / OPTIONAL classification badge, full technical
description, approved repair method with material call-outs, and four
engineering approval sign-off blocks (Design Engineer / DER / QA /
Approving Authority).

---

## Quick Start

> **Primary execution environment: Google Colab.** The dependencies
> (OpenCV, Gradio, ReportLab) are pre-available or install in seconds on Colab.

### 1. Clone and install

```bash
git clone https://github.com/Amg920624/aero-quality-inspector.git
cd aero-quality-inspector
pip install -r requirements.txt
```

### 2. Launch the dashboard

```bash
python app.py
```

Open the local URL printed by Gradio (e.g. `http://127.0.0.1:7860`).

### 3. Run an inspection

1. Upload a surface image (BMP, PNG, JPG).
2. Enter a **Part Number** and **Aircraft Zone** (optional — defaults are used if left blank).
3. Click **Run Inspection**.
4. Review the Canny edge map, classification card, and engineering advisory.
5. Download the NCR, Work Order, and Engineering Order PDFs.

### Run inspector standalone (no UI)

```bash
python inspector.py
```

Fetches NEU dataset samples (or generates synthetic images if offline),
classifies all four defect types, and writes `report.txt`.

### Run advisor self-test

```bash
python advisor.py
```

Exercises all defect types across representative density values and prints
formatted advisory reports to stdout.

---

## Sample Output

```
=============================== ENGINEERING ADVISORY REPORT ================================
Defect Type    : CRAZING
Edge Density   : 0.0921
Decision       : MONITOR
FAA Reference  : AC 43.13-1B Chapter 3, Section 3-6; Chapter 5, Section 5-4
Threshold Note : Crazing extends toward substrate; stress concentrations present

Repair Procedure:
  Dye-penetrant inspection mandatory. If cracks < 0.005 in. deep, sand,
  apply fibre-reinforced filler, and re-inspect within 25 flight hours.
============================================================================================
```

Three PDFs are saved to `generated_docs/` with document numbers in the format
`NCR-YYYYMMDD-XXXXXX.pdf`, `WO-YYYYMMDD-XXXXXX.pdf`, `EO-YYYYMMDD-XXXXXX.pdf`.

---

## Stack

- Python 3.10+
- [OpenCV](https://opencv.org/) — edge detection and image processing
- [Gradio](https://www.gradio.app/) — web dashboard
- [ReportLab](https://www.reportlab.com/) — PDF generation
- [NumPy](https://numpy.org/) — array operations

---

## Author

Built by an aerospace engineer in Montreal.

[linkedin.com/in/aaron-mandujano-289778161](https://www.linkedin.com/in/aaron-mandujano-289778161)
