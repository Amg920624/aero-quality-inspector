# aero-quality-inspector — CLAUDE.md

## Project context
Aerospace surface defect inspection system built by an aerospace engineer 
in Montreal. Detects defect types in component images (crazing, inclusion, 
pitting, scratch) and auto-generates engineering work orders with disposition 
recommendations based on engineering standards.

This is a public portfolio project. Code quality and documentation matter 
for professional visibility.

Repo: github.com/Amg920624/aero-quality-inspector
Author LinkedIn: linkedin.com/in/aaron-mandujano-289778161

## Architecture — what each file does
- app.py               → Entry point. Orchestrates the full pipeline
- inspector.py         → Defect classification from images (computer vision)
- advisor.py           → Evaluates findings against standards, determines disposition
- document_generator.py → Generates the engineering work order document
- engineering_standards.json → Rules/thresholds for each defect type
- report.txt           → Sample output (do not modify manually)

## Defect types the system handles
- crazing    → network of fine surface cracks
- inclusion  → foreign material embedded in surface
- pitting    → small cavities or voids
- scratch    → linear surface damage

## Stack
- Python 3.10+
- Read requirements.txt before suggesting new dependencies
- Primary execution environment: Google Colab (not local machine)
- No heavy ML libs installed locally — they live in Colab

## Coding conventions
- Docstrings in English (public repo)
- Internal comments in Spanish are fine
- Type hints on all functions
- No hardcoded paths — use relative paths or env variables
- No notebook outputs committed to git

## Git rules
- Commits in English, descriptive messages
- Conventional commits: feat:, fix:, docs:, refactor:, test:
- One feature = one branch = one PR
- Never push directly to main without a PR

## What NOT to do
- Do not modify engineering_standards.json without explicit instruction
- Do not refactor the 3-module architecture (inspector/advisor/document) 
  without discussion — it reflects a real industrial workflow separation
- Do not add dependencies not in requirements.txt without asking first

## Lessons learned
(This section grows over time — add entries when Claude makes a mistake 
that should not repeat)
