import os
import cv2
import numpy as np
import json
import tensorflow as tf
from ultralytics import YOLO
from tensorflow.keras.utils import load_img, img_to_array

DETECT_CONFIDENCE = 0.65
ENLARGE_SCALE = 1.75
CROP_SCALE_FACTOR = 4.5

def enlarge_bbox(x1, y1, x2, y2, scale, img_width, img_height):
    w = x2 - x1
    h = y2 - y1
    cx = x1 + w / 2
    cy = y1 + h / 2

    new_w = w * scale
    new_h = h * scale

    new_x1 = max(0, int(cx - new_w / 2))
    new_y1 = max(0, int(cy - new_h / 2))
    new_x2 = min(img_width, int(cx + new_w / 2))
    new_y2 = min(img_height, int(cy + new_h / 2))

    return new_x1, new_y1, new_x2, new_y2

def annotate_image_with_predictions(img, boxes, predictions, save_path):
    annotated_img = img.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 2

    for i, (x1, y1, x2, y2) in enumerate(boxes):
        label = predictions.get(f"crop_{i}.jpg", None)
        if label:
            confidence = label["confidence"]
            if confidence < 0.5:
                color = (153, 153, 255)
            elif confidence < 0.75:
                color = (153, 255, 255)
            else:
                color = (153, 255, 153)

            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

            text = label["class"]
            # Calculate text size and position
            (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, font_thickness)
            text_x = x1
            text_y = y1 - 10 if y1 - 10 > text_h else y1 + text_h + 10

            # Draw text background for better visibility
            cv2.rectangle(
                annotated_img,
                (text_x, text_y - text_h - baseline),
                (text_x + text_w, text_y + baseline),
                (0, 0, 0),
                thickness=cv2.FILLED,
            )

            # Put text over rectangle
            cv2.putText(
                annotated_img, text, (text_x, text_y), font, font_scale, color, font_thickness, lineType=cv2.LINE_AA
            )

    cv2.imwrite(save_path, annotated_img)

def create_classification_image(crop_img, class_name, confidence, save_path):
    pad = 5
    crop_img_padded = cv2.copyMakeBorder(crop_img, pad, pad, pad, pad, borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])

    crop_h, crop_w = crop_img_padded.shape[:2]
    panel_w = int(crop_w * 1.4)
    panel_h = crop_h
    
    if confidence < 0.5:
        base_color = (153, 153, 255)
    elif confidence < 0.75:
        base_color = (153, 255, 255)
    else:
        base_color = (153, 255, 153)

    crop_bg = np.full((crop_h, crop_w, 3), base_color, dtype=np.uint8)
    panel = np.full((panel_h, panel_w, 3), base_color, dtype=np.uint8)

    border_thickness = 5
    crop_bg[border_thickness:-border_thickness, border_thickness:-border_thickness] = crop_img_padded[border_thickness:-border_thickness, border_thickness:-border_thickness]

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    font_thickness = 2

    text_class = f"Class: {class_name}"
    text_conf = f"Confidence: {confidence*100:.2f}%"

    (w_class, h_class), _ = cv2.getTextSize(text_class, font, font_scale, font_thickness)
    (w_conf, h_conf), _ = cv2.getTextSize(text_conf, font, font_scale, font_thickness)

    total_text_height = h_class + h_conf + 20
    y_start = (panel_h - total_text_height) // 2 + h_class

    shadow_offset = 2
    text_shadow = (30, 30, 30)
    text_color = (255, 255, 255)

    cv2.putText(panel, text_class, (20 + shadow_offset, y_start + shadow_offset), font, font_scale, text_shadow, font_thickness + 1, lineType=cv2.LINE_AA)
    cv2.putText(panel, text_conf, (20 + shadow_offset, y_start + h_class + 20 + shadow_offset), font, font_scale, text_shadow, font_thickness + 1, lineType=cv2.LINE_AA)
    
    cv2.putText(panel, text_class, (20, y_start), font, font_scale, text_color, font_thickness, lineType=cv2.LINE_AA)
    cv2.putText(panel, text_conf, (20, y_start + h_class + 20), font, font_scale, text_color, font_thickness, lineType=cv2.LINE_AA)

    if panel.shape[0] < crop_bg.shape[0]:
        diff = crop_bg.shape[0] - panel.shape[0]
        top_pad = diff // 2
        bottom_pad = diff - top_pad
        panel = cv2.copyMakeBorder(panel, top_pad, bottom_pad, 0, 0, borderType=cv2.BORDER_CONSTANT, value=base_color)
    elif panel.shape[0] > crop_bg.shape[0]:
        diff = panel.shape[0] - crop_bg.shape[0]
        top_pad = diff // 2
        bottom_pad = diff - top_pad
        crop_bg = cv2.copyMakeBorder(crop_bg, top_pad, bottom_pad, 0, 0, borderType=cv2.BORDER_CONSTANT, value=base_color)

    combined_img = np.hstack((crop_bg, panel))

    cv2.imwrite(save_path, combined_img, [cv2.IMWRITE_JPEG_QUALITY, 95])


class JerawatDetectionService:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, image_path):
        results = self.model.predict(
            source=image_path,
            conf=DETECT_CONFIDENCE,
            save=False,
            imgsz=640,
            device='cpu'
        )
        img = cv2.imread(image_path)
        img_height, img_width = img.shape[:2]

        boxes = []
        for box in results[0].boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = box[:4]
            boxes.append((
                int(x1), int(y1), int(x2), int(y2)
            ))

        return boxes, img

class JerawatClassificationService:
    def __init__(self, model_path, class_index_path):
        self.model_path = model_path
        self.class_names = self._load_class_indices(class_index_path)
        self.interpreter = self._load_model()

        input_details = self.interpreter.get_input_details()
        self.input_shape = input_details[0]['shape']
        self.target_size = (self.input_shape[2], self.input_shape[1])

    def _load_class_indices(self, path):
        with open(path, "r") as f:
            class_indices = json.load(f)
        return {int(v): k for k, v in class_indices.items()}

    def _load_model(self):
        interpreter = tf.lite.Interpreter(model_path=self.model_path)
        interpreter.allocate_tensors()
        return interpreter

    def predict(self, img_path):
        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()

        img = load_img(img_path, target_size=self.target_size)
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array.astype(np.float32), axis=0)

        self.interpreter.set_tensor(input_details[0]['index'], img_array)
        self.interpreter.invoke()

        prediction = self.interpreter.get_tensor(output_details[0]['index'])[0]
        predicted_index = np.argmax(prediction)
        return {
            "class": self.class_names[predicted_index],
            "confidence": round(float(prediction[predicted_index]), 4)
        }

class JerawatPipeline:
    def __init__(self, deteksi_model_path, klasifikasi_model_path, class_index_path, crop_folder="hasil_crop"):
        self.detector = JerawatDetectionService(deteksi_model_path)
        self.classifier = JerawatClassificationService(klasifikasi_model_path, class_index_path)
        self.crop_folder = crop_folder
        os.makedirs(self.crop_folder, exist_ok=True)

    def process(self, image_path):
        detected_boxes, img = self.detector.detect(image_path)
        img_height, img_width = img.shape[:2]

        if not detected_boxes:
            return {"message": "jerawat tidak ditemukan"}

        results = {}
        os.makedirs("hasil_klasifikasi", exist_ok=True)

        for i, (x1, y1, x2, y2) in enumerate(detected_boxes):
            x1, y1, x2, y2 = enlarge_bbox(x1, y1, x2, y2, ENLARGE_SCALE, img_width, img_height)

            crop = img[y1:y2, x1:x2]
            resized_crop = cv2.resize(crop, None, fx=CROP_SCALE_FACTOR, fy=CROP_SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)
            crop_path = f"{self.crop_folder}/crop_{i}.jpg"
            cv2.imwrite(crop_path, resized_crop)

            prediction = self.classifier.predict(crop_path)
            results[os.path.basename(crop_path)] = prediction

            save_path = f"hasil_klasifikasi/classified_{i}.jpg"
            create_classification_image(resized_crop, prediction["class"], prediction["confidence"], save_path)

        annotate_image_with_predictions(img, detected_boxes, results, "hasil_klasifikasi/annotated_image.jpg")

        return results

if __name__ == "__main__":
    pipeline = JerawatPipeline(
        deteksi_model_path="model/deteksi/best.pt",
        klasifikasi_model_path="model/klasifikasi/model.tflite",
        class_index_path="class_indices.json"
    )

    result = pipeline.process("images.jpg")
    print(json.dumps(result, indent=4))
