"""
app.py – Gradio dashboard for the Aero Quality Inspector.

Workflow:
  1. User uploads an image.
  2. inspector.py classifies the defect and produces an edge map.
  3. advisor.py loads engineering_standards.json and returns ACCEPT/MONITOR/REJECT.
  4. Dashboard displays: original image | edge map | classification | advisory.
"""

import tempfile
import os

import cv2
import gradio as gr
import numpy as np

from inspector import run_inspection
from advisor import get_advisory, format_advisory, load_standards

# Load standards once at startup
_STANDARDS = load_standards()

DECISION_COLOURS = {
    "ACCEPT":  "#28a745",   # green
    "MONITOR": "#fd7e14",   # orange
    "REJECT":  "#dc3545",   # red
}


def inspect_and_advise(image: np.ndarray):
    """Core pipeline called by Gradio on every image upload.

    Parameters
    ----------
    image : np.ndarray
        RGB image array provided by gr.Image (type='numpy').

    Returns
    -------
    tuple of (edge_map_rgb, classification_html, advisory_text)
    """
    if image is None:
        return None, "<p>No image provided.</p>", "Upload an image to begin."

    # Save the uploaded image to a temp file so inspector.py can read it
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_in:
        tmp_in_path = tmp_in.name
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        # Gradio gives RGB; OpenCV expects BGR
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(tmp_in_path, bgr)

        label, edge_pixels, density, confidence = run_inspection(tmp_in_path, tmp_out_path)

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
      <td>{confidence:.1%}</td>
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
  </table>
</div>
"""
    finally:
        for p in (tmp_in_path, tmp_out_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    return edge_rgb, classification_html, advisory_text


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(
    title="Aero Quality Inspector",
    theme=gr.themes.Base(),
    css="""
        #title { text-align:center; }
        #advisory-box textarea { font-family: monospace !important; font-size: 0.85em !important; }
    """,
) as demo:

    gr.Markdown(
        "# Aero Quality Inspector\n"
        "Upload a surface image to detect defects (scratch / pitting / crazing / inclusion) "
        "and receive an FAA AC 43.13-based engineering advisory.",
        elem_id="title",
    )

    with gr.Row():
        with gr.Column(scale=1):
            input_image = gr.Image(
                label="Upload Surface Image",
                type="numpy",
                image_mode="RGB",
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

    run_btn.click(
        fn=inspect_and_advise,
        inputs=input_image,
        outputs=[edge_output, classification_output, advisory_output],
    )

    # Also run on image upload for instant feedback
    input_image.change(
        fn=inspect_and_advise,
        inputs=input_image,
        outputs=[edge_output, classification_output, advisory_output],
    )

if __name__ == "__main__":
    demo.launch(share=False)
