"""
advisor.py – Engineering advisory module for the Aero Quality Inspector.

Loads FAA AC 43.13-based standards from engineering_standards.json and
returns an ACCEPT / MONITOR / REJECT decision with the relevant repair
procedure for a given defect type and edge-density value.
"""

import json
import os
from dataclasses import dataclass


STANDARDS_PATH = os.path.join(os.path.dirname(__file__), "engineering_standards.json")


@dataclass
class AdvisoryResult:
    defect_type: str
    density: float
    decision: str          # "ACCEPT", "MONITOR", or "REJECT"
    faa_reference: str
    threshold_note: str
    repair_procedure: str


def load_standards(path: str = STANDARDS_PATH) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def get_advisory(defect_type: str, density: float, standards: dict | None = None) -> AdvisoryResult:
    """Return an engineering advisory for the given defect type and density.

    Parameters
    ----------
    defect_type : str
        One of "scratch", "pitting", "crazing", "inclusion", "clean".
    density : float
        Edge-pixel density (0.0 – 1.0) from the inspector.
    standards : dict, optional
        Pre-loaded standards dict; loaded from file if not supplied.

    Returns
    -------
    AdvisoryResult
        Dataclass with decision, FAA reference, threshold note, and repair procedure.
    """
    if standards is None:
        standards = load_standards()

    defect_standards = standards.get("defect_standards", {})

    # Normalise label differences (inspector uses "pitting", json uses "pitting")
    key = defect_type.lower().strip()
    if key not in defect_standards:
        # Fallback: unknown type → reject to be safe
        return AdvisoryResult(
            defect_type=defect_type,
            density=density,
            decision="REJECT",
            faa_reference="Unknown defect type – consult DER",
            threshold_note="No standard available for this defect classification.",
            repair_procedure="Remove from service. Submit to a licensed A&P mechanic for evaluation.",
        )

    spec = defect_standards[key]
    thresholds = spec["thresholds"]
    repair_procedures = spec["repair_procedures"]
    faa_ref = spec.get("faa_reference", "AC 43.13-1B")

    # Evaluate in order: ACCEPT → MONITOR → REJECT
    if density <= thresholds["accept"]["max_density"]:
        decision = "ACCEPT"
    elif density <= thresholds["monitor"]["max_density"]:
        decision = "MONITOR"
    else:
        decision = "REJECT"

    decision_key = decision.lower()
    note = thresholds[decision_key]["note"]
    repair = repair_procedures[decision_key]

    return AdvisoryResult(
        defect_type=defect_type,
        density=density,
        decision=decision,
        faa_reference=faa_ref,
        threshold_note=note,
        repair_procedure=repair,
    )


def format_advisory(result: AdvisoryResult) -> str:
    """Return a human-readable advisory string."""
    bar = "=" * 60
    return (
        f"{bar}\n"
        f"ENGINEERING ADVISORY REPORT\n"
        f"{bar}\n"
        f"Defect Type    : {result.defect_type.upper()}\n"
        f"Edge Density   : {result.density:.4f}\n"
        f"Decision       : {result.decision}\n"
        f"FAA Reference  : {result.faa_reference}\n"
        f"Threshold Note : {result.threshold_note}\n"
        f"\nRepair Procedure:\n  {result.repair_procedure}\n"
        f"{bar}"
    )


if __name__ == "__main__":
    # Quick self-test across representative densities
    test_cases = [
        ("scratch",   0.015),
        ("scratch",   0.032),
        ("scratch",   0.048),
        ("pitting",   0.008),
        ("pitting",   0.015),
        ("pitting",   0.022),
        ("crazing",   0.055),
        ("crazing",   0.090),
        ("crazing",   0.130),
        ("inclusion", 0.150),
        ("inclusion", 0.200),
        ("inclusion", 0.250),
        ("clean",     0.002),
    ]

    standards = load_standards()
    for defect_type, density in test_cases:
        result = get_advisory(defect_type, density, standards)
        print(format_advisory(result))
        print()
