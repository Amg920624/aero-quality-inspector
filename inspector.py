import sys
import math
import cv2
import numpy as np
import urllib.request
import os


def download_mvtec_wood_sample(dest_path="wood_sample.png"):
    """Try to download a wood texture sample from MVTec dataset."""
    url = "https://www.mvtec.com/fileadmin/Redaktion/mvtec.com/company/research/datasets/mvtec_ad/wood/test/scratch/000.png"
    try:
        urllib.request.urlretrieve(url, dest_path)
        img = cv2.imread(dest_path)
        if img is not None:
            return dest_path
    except Exception:
        pass
    return None


def create_synthetic_wood_defect(dest_path="wood_sample.png"):
    """Create a synthetic wood-like image with a scratch defect."""
    h, w = 256, 256
    # Wood-like base: horizontal grain using Perlin-style noise approximation
    img = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        base = 120 + 30 * np.sin(y / 8.0)
        noise = np.random.randint(-15, 15, w).astype(np.float32)
        img[y] = np.clip(base + noise, 0, 255).astype(np.uint8)

    # Add a scratch defect (bright diagonal line)
    cv2.line(img, (40, 60), (200, 180), 240, thickness=3)
    # Add a dark pit defect
    cv2.ellipse(img, (160, 80), (12, 6), 30, 0, 360, 40, thickness=-1)

    color_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    # Tint brown for wood appearance
    color_img[:, :, 0] = (color_img[:, :, 0] * 0.4).astype(np.uint8)
    color_img[:, :, 1] = (color_img[:, :, 1] * 0.6).astype(np.uint8)

    cv2.imwrite(dest_path, color_img)
    return dest_path


def compute_confidence(density, threshold):
    """Confidence score in [0.5, 1.0] for the classification label.

    Uses a sigmoid centered at threshold so that confidence is ~0.5 when
    density is right at the threshold, and approaches 1.0 as density moves
    further away in either direction.
    """
    k = 10.0
    x = k * (density - threshold) / max(threshold, 1e-9)
    sigmoid = 1.0 / (1.0 + math.exp(-x))
    return sigmoid if density >= threshold else 1.0 - sigmoid


def classify_defect(edges, threshold_density=0.005):
    """Classify image as defect_detected or clean based on edge density.

    Edge density = edge pixels / total pixels.
    Above threshold => defect_detected.
    Returns label, edge pixel count, density, and confidence score.
    """
    total_pixels = edges.shape[0] * edges.shape[1]
    edge_pixels = int(np.count_nonzero(edges))
    density = edge_pixels / total_pixels
    label = "defect_detected" if density >= threshold_density else "clean"
    confidence = compute_confidence(density, threshold_density)
    return label, edge_pixels, density, confidence


def run_inspection(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from '{image_path}'")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, threshold1=100, threshold2=200)
    cv2.imwrite("output.png", edges)

    label, edge_pixels, density, confidence = classify_defect(edges)
    return label, edge_pixels, density, confidence


def main():
    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
        if not os.path.exists(image_path):
            print(f"Error: file not found: '{image_path}'")
            sys.exit(1)
    else:
        print("No image provided — attempting to download MVTec wood sample...")
        image_path = download_mvtec_wood_sample()
        if image_path is None:
            print("Download failed — generating synthetic defect image.")
            image_path = create_synthetic_wood_defect()
        else:
            print(f"Downloaded sample: {image_path}")

    label, edge_pixels, density, confidence = run_inspection(image_path)

    report = (
        f"MVTec Defect Detection Report\n"
        f"==============================\n"
        f"Image          : {image_path}\n"
        f"Result         : {label}\n"
        f"Confidence     : {confidence:.4f}\n"
        f"Edge pixels    : {edge_pixels}\n"
        f"Edge density   : {density:.4f}\n"
        f"Threshold      : 0.0050\n"
    )

    with open("report.txt", "w") as f:
        f.write(report)

    print(report.strip())
    print("\nDefect scan complete. Edge map saved to output.png, report saved to report.txt")


if __name__ == "__main__":
    main()
