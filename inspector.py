import sys
import cv2

def main():
    if len(sys.argv) < 2:
        print("Usage: python inspector.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: could not load image from '{image_path}'")
        sys.exit(1)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, threshold1=100, threshold2=200)

    cv2.imwrite("output.png", edges)
    print("Defect scan complete")

if __name__ == "__main__":
    main()
