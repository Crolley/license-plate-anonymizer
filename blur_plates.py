import cv2
import os
import numpy as np
from ultralytics import YOLO

INPUT_DIR = "photos"
OUTPUT_DIR = "output"
MODEL_PATH = "license_plate_detector.pt"

model = YOLO(MODEL_PATH)


def blur_with_rounded_corners(img, x1, y1, x2, y2, radius=25):
    roi = img[y1:y2, x1:x2]
    if roi.size == 0:
        return

    blurred = cv2.GaussianBlur(roi, (99, 99), 30)

    h, w = roi.shape[:2]
    radius = min(radius, w // 2, h // 2)

    mask = np.zeros((h, w), dtype=np.uint8)

    cv2.rectangle(mask, (radius, 0), (w - radius, h), 255, -1)
    cv2.rectangle(mask, (0, radius), (w, h - radius), 255, -1)

    cv2.circle(mask, (radius, radius), radius, 255, -1)
    cv2.circle(mask, (w - radius, radius), radius, 255, -1)
    cv2.circle(mask, (radius, h - radius), radius, 255, -1)
    cv2.circle(mask, (w - radius, h - radius), radius, 255, -1)

    mask = cv2.merge([mask, mask, mask])
    img[y1:y2, x1:x2] = np.where(mask == 255, blurred, roi)


for root, _, files in os.walk(INPUT_DIR):
    for filename in files:
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        input_path = os.path.join(root, filename)

        rel_path = os.path.relpath(root, INPUT_DIR)
        output_dir = os.path.join(OUTPUT_DIR, rel_path)
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, filename)

        img = cv2.imread(input_path)
        if img is None:
            continue

        results = model(img, conf=0.3)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(img.shape[1], x2)
                y2 = min(img.shape[0], y2)

                blur_with_rounded_corners(img, x1, y1, x2, y2)

        cv2.imwrite(output_path, img)
        print(output_path)

print("Done.")
