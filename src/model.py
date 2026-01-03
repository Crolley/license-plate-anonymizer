import cv2
import numpy as np
from ultralytics import YOLO
import os
import zipfile
import shutil


class LicensePlateProcessor:

    def __init__(self, model_path="license_plate_detector.pt"):
        self.model_path = model_path
        self.model = None

    def load_model(self):
        if self.model is None:
            self.model = YOLO(self.model_path)
        return self.model

    def blur_with_rounded_corners(self, img, x1, y1, x2, y2, radius=25):
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

    def process_image(self, input_path, output_path, confidence=0.3):
        img = cv2.imread(input_path)
        if img is None:
            return False

        if self.model is None:
            self.load_model()

        results = self.model(img, conf=confidence)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(img.shape[1], x2)
                y2 = min(img.shape[0], y2)
                self.blur_with_rounded_corners(img, x1, y1, x2, y2)

        cv2.imwrite(output_path, img)
        return True

    def collect_images_from_files(self, file_paths):
        images = []
        for file_path in file_paths:
            images.append((file_path, os.path.basename(file_path)))
        return images

    def collect_images_from_folder(self, folder_path):
        images = []
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    input_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(root, folder_path)
                    output_rel_path = os.path.join(rel_path, filename)
                    images.append((input_path, output_rel_path))
        return images

    def process_batch(self, images, output_dir, progress_callback=None):
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        self.load_model()

        total = len(images)
        success_count = 0

        for i, (input_path, rel_path) in enumerate(images, 1):
            if progress_callback:
                progress_callback(i, total, os.path.basename(input_path))

            output_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if self.process_image(input_path, output_path):
                success_count += 1

        return success_count

    @staticmethod
    def create_zip(source_dir, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False
