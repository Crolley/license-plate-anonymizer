import cv2
import os
import numpy as np
from ultralytics import YOLO

INPUT_DIR = "photos"
OUTPUT_DIR = "output"
MODEL_PATH = "license_plate_detector.pt"

model = YOLO(MODEL_PATH)


def blur_rotated_plate(img, box_points):
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
            # Vérifier si on a des OBB (Oriented Bounding Boxes) pour la rotation
            if hasattr(r, 'obb') and r.obb is not None and len(r.obb) > 0:
                # Mode avec rotation (si le modèle supporte OBB)
                for obb in r.obb:
                    # Récupérer les 4 points du polygone roté
                    points = obb.xyxyxyxy[0].cpu().numpy()
                    blur_rotated_plate(img, points)
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

                    blur_rotated_plate(img, box_points)

        cv2.imwrite(output_path, img)
        print(output_path)

print("Done.")
