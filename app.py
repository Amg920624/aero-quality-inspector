"""
app.py – Gradio dashboard for the Aero Quality Inspector.

Workflow:
  1. User uploads an image.
  2. inspector.py classifies the defect and produces an edge map.
  3. advisor.py loads engineering_standards.json and returns ACCEPT/MONITOR/REJECT.
  4. document_generator.py creates NCR, Work Order, and Engineering Order PDFs.
  5. Dashboard displays: original image | edge map | classification | advisory
     and provides download buttons for all three documents.
"""

import tempfile
import os

import cv2
import gradio as gr
import numpy as np

from inspector import run_inspection
from advisor import get_advisory, format_advisory, load_standards
from document_generator import (
    generate_ncr,
    generate_work_order,
    generate_engineering_order,
)

# Load standards once at startup
_STANDARDS = load_standards()

DECISION_COLOURS = {
    "ACCEPT":  "#28a745",   # green
    "MONITOR": "#fd7e14",   # orange
    "REJECT":  "#dc3545",   # red
}

# Default placeholder values for document fields
DEFAULT_PART_NUMBER = "PN-00000"
DEFAULT_ZONE        = "ZONE-A"


def inspect_and_advise(
    image: np.ndarray,
    part_number: str,
    zone: str,
):
    """Core pipeline called by Gradio on every inspection run.

    Parameters
    ----------
    image       : RGB image array provided by gr.Image (type='numpy').
    part_number : Aircraft part number entered by the user.
    zone        : Aircraft zone / station entered by the user.

    Returns
    -------
    tuple of (edge_map_rgb, classification_html, advisory_text,
              ncr_path, wo_path, eo_path)
    """
    no_docs = (None, None, None)

    if image is None:
        return None, "<p>No image provided.</p>", "Upload an image to begin.", *no_docs

    part_number = part_number.strip() or DEFAULT_PART_NUMBER
    zone        = zone.strip()        or DEFAULT_ZONE

    # Save the uploaded image to a temp file so inspector.py can read it
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_in:
        tmp_in_path = tmp_in.name
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        # Gradio gives RGB; OpenCV expects BGR
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(tmp_in_path, bgr)

        label, edge_pixels, density, confidence_score = run_inspection(tmp_in_path, tmp_out_path)

        # Load edge map and convert back to RGB for Gradio
        edge_bgr = cv2.imread(tmp_out_path, cv2.IMREAD_GRAYSCALE)
        edge_rgb = cv2.cvtColor(edge_bgr, cv2.COLOR_GRAY2RGB)

        # Engineering advisory
        advisory = get_advisory(label, density, _STANDARDS)
        advisory_text = format_advisory(advisory)

        # Styled classification card
        decision_colour = DECISION_COLOURS.get(advisory.decision, "#6c757d")
        classification_html = f"""
<div style="font-family: monospace; padding: 16px; border-radius: 8px;
            background: #1e1e2e; color: #cdd6f4; line-height: 1.8;">
  <h3 style="margin:0 0 12px; color:#89dceb;">Surface Defect Classification</h3>
  <table style="width:100%; border-collapse:collapse;">
    <tr>
      <td style="color:#a6adc8; width:45%;">Detected Defect</td>
      <td><strong style="color:#f38ba8; font-size:1.1em;">{label.upper()}</strong></td>
    </tr>
    <tr>
      <td style="color:#a6adc8;">Edge Pixels</td>
      <td>{edge_pixels:,}</td>
    </tr>
    <tr>
      <td style="color:#a6adc8;">Edge Density</td>
      <td>{density:.4f}</td>
    </tr>
    <tr>
      <td style="color:#a6adc8;">Confidence</td>
      <td>{confidence_score:.1%}</td>
    </tr>
    <tr>
      <td style="color:#a6adc8;">Engineering Decision</td>
      <td>
        <span style="background:{decision_colour}; color:#fff; padding:3px 10px;
                     border-radius:4px; font-weight:bold;">
          {advisory.decision}
        </span>
      </td>
    </tr>
    <tr>
      <td style="color:#a6adc8;">FAA Reference</td>
      <td style="font-size:0.85em; color:#bac2de;">{advisory.faa_reference}</td>
    </tr>
    <tr>
      <td style="color:#a6adc8;">Part Number</td>
      <td style="font-size:0.85em;">{part_number}</td>
    </tr>
    <tr>
      <td style="color:#a6adc8;">Aircraft Zone</td>
      <td style="font-size:0.85em;">{zone}</td>
    </tr>
  </table>
</div>
"""

        # Generate all three documents
        ncr_path = generate_ncr(
            defect_type=label,
            decision=advisory.decision,
            density=density,
            confidence=confidence_score,
            part_number=part_number,
            zone=zone,
        )
        wo_path = generate_work_order(
            defect_type=label,
            repair_procedure=advisory.repair_procedure,
            part_number=part_number,
        )
        eo_path = generate_engineering_order(
            defect_type=label,
            decision=advisory.decision,
            regulatory_ref=advisory.faa_reference,
        )

    finally:
        for p in (tmp_in_path, tmp_out_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    return edge_rgb, classification_html, advisory_text, ncr_path, wo_path, eo_path


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(
    title="Aero Quality Inspector",
    theme=gr.themes.Base(),
    css="""
        #title { text-align:center; }
        #advisory-box textarea { font-family: monospace !important; font-size: 0.85em !important; }
        #docs-section { border-top: 2px solid #2c6fad; margin-top: 8px; padding-top: 8px; }
    """,
) as demo:

    gr.Markdown(
        "# Aero Quality Inspector\n"
        "Upload a surface image to detect defects (scratch / pitting / crazing / inclusion) "
        "and receive an FAA AC 43.13-based engineering advisory with auto-generated compliance documents.",
        elem_id="title",
    )

    with gr.Row():
        with gr.Column(scale=1):
            input_image = gr.Image(
                label="Upload Surface Image",
                type="numpy",
                image_mode="RGB",
            )
            with gr.Row():
                part_number_input = gr.Textbox(
                    label="Part Number",
                    placeholder=DEFAULT_PART_NUMBER,
                    value="",
                )
                zone_input = gr.Textbox(
                    label="Aircraft Zone / Station",
                    placeholder=DEFAULT_ZONE,
                    value="",
                )
            run_btn = gr.Button("Run Inspection", variant="primary")

        with gr.Column(scale=1):
            edge_output = gr.Image(label="Canny Edge Map", type="numpy")

    with gr.Row():
        classification_output = gr.HTML(label="Classification")

    with gr.Row():
        advisory_output = gr.Textbox(
            label="Engineering Advisory (FAA AC 43.13)",
            lines=14,
            interactive=False,
            elem_id="advisory-box",
        )

    # Document download section
    gr.Markdown("### Generated Compliance Documents", elem_id="docs-section")
    with gr.Row():
        ncr_download = gr.File(
            label="Non-Conformance Report (NCR)",
            interactive=False,
        )
        wo_download = gr.File(
            label="Work Order (WO)",
            interactive=False,
        )
        eo_download = gr.File(
            label="Engineering Order (EO)",
            interactive=False,
        )

    # Example images shipped with the repo
    example_files = [
        f for f in ["scratch_1.bmp", "pitted_1.bmp", "crazing_1.bmp", "inclusion_1.bmp"]
        if os.path.exists(f)
    ]
    if example_files:
        gr.Examples(
            examples=example_files,
            inputs=input_image,
            label="Example Images (NEU dataset samples)",
        )

    _outputs = [
        edge_output,
        classification_output,
        advisory_output,
        ncr_download,
        wo_download,
        eo_download,
    ]
    _inputs = [input_image, part_number_input, zone_input]

    run_btn.click(
        fn=inspect_and_advise,
        inputs=_inputs,
        outputs=_outputs,
    )

    # Also run on image upload for instant feedback
    input_image.change(
        fn=inspect_and_advise,
        inputs=_inputs,
        outputs=_outputs,
    )

if __name__ == "__main__":
    demo.launch(share=False)
