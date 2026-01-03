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

    def blur_rotated_plate(self, img, box_points):
        """
        Floute une plaque d'immatriculation en suivant sa rotation.
        box_points: 4 points du polygone de la plaque (numpy array de forme (4, 2))
        """
        # Créer un masque pour la zone à flouter
        mask = np.zeros(img.shape[:2], dtype=np.uint8)

        # Réduire très légèrement la zone pour ne pas déborder
        center = np.mean(box_points, axis=0)
        reduced_points = []
        for point in box_points:
            direction = point - center
            reduced_point = center + direction * 0.95  # Réduction de seulement 5%
            reduced_points.append(reduced_point)

        reduced_points = np.array(reduced_points, dtype=np.int32)

        # Remplir le polygone dans le masque
        cv2.fillPoly(mask, [reduced_points], 255)

        # Appliquer un léger lissage au masque pour des bords plus doux
        mask = cv2.GaussianBlur(mask, (15, 15), 0)

        # Flouter toute l'image
        blurred_img = cv2.GaussianBlur(img, (99, 99), 30)

        # Mélanger l'image originale et l'image floutée selon le masque
        mask_3ch = cv2.merge([mask, mask, mask]) / 255.0
        img[:] = (blurred_img * mask_3ch + img * (1 - mask_3ch)).astype(np.uint8)

    def process_image(self, input_path, output_path, confidence=0.3):
        img = cv2.imread(input_path)
        if img is None:
            return False

        if self.model is None:
            self.load_model()

        results = self.model(img, conf=confidence)

        for r in results:
            # Vérifier si on a des OBB (Oriented Bounding Boxes) pour la rotation
            if hasattr(r, 'obb') and r.obb is not None and len(r.obb) > 0:
                # Mode avec rotation (si le modèle supporte OBB)
                for obb in r.obb:
                    # Récupérer les 4 points du polygone roté
                    points = obb.xyxyxyxy[0].cpu().numpy()
                    self.blur_rotated_plate(img, points)
            else:
                # Mode classique avec rectangles alignés
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Réduire la zone de floutage pour qu'elle soit plus précise
                    width = x2 - x1
                    height = y2 - y1
                    margin_x = int(width * 0.02)  # Réduction de 2% en largeur (presque rien)
                    margin_y = int(height * 0.15)  # Réduction de 15% en hauteur

                    x1 = max(0, x1 + margin_x)
                    y1 = max(0, y1 + margin_y)
                    x2 = min(img.shape[1], x2 - margin_x)
                    y2 = min(img.shape[0], y2 - margin_y)

                    # Créer 4 points pour un rectangle non-roté
                    box_points = np.array([
                        [x1, y1],
                        [x2, y1],
                        [x2, y2],
                        [x1, y2]
                    ], dtype=np.float32)

                    self.blur_rotated_plate(img, box_points)

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
