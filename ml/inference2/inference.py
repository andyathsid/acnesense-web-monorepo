import os
import cv2
from datetime import datetime
import numpy as np
import json
import tensorflow as tf
from tensorflow.keras.utils import load_img, img_to_array

DETECT_CONFIDENCE = 0.30
CLASSIFY_CONFIDENCE = 0.50
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

def non_max_suppression(boxes, scores, iou_threshold=0.5):
    if len(boxes) == 0:
        return []
    
    boxes = np.array(boxes)
    scores = np.array(scores)
    
    indices = np.argsort(scores)[::-1]
    
    keep = []
    while len(indices) > 0:
        current = indices[0]
        keep.append(current)
        
        if len(indices) == 1:
            break
            
        current_box = boxes[current]
        remaining_boxes = boxes[indices[1:]]
        
        x1 = np.maximum(current_box[0], remaining_boxes[:, 0])
        y1 = np.maximum(current_box[1], remaining_boxes[:, 1])
        x2 = np.minimum(current_box[2], remaining_boxes[:, 2])
        y2 = np.minimum(current_box[3], remaining_boxes[:, 3])
        
        intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        
        area_current = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
        area_remaining = (remaining_boxes[:, 2] - remaining_boxes[:, 0]) * (remaining_boxes[:, 3] - remaining_boxes[:, 1])
        union = area_current + area_remaining - intersection
        
        iou = intersection / (union + 1e-6)
        
        indices = indices[1:][iou < iou_threshold]
    
    return [boxes[i] for i in keep], [scores[i] for i in keep]

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
            (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, font_thickness)
            text_x = x1
            text_y = y1 - 10 if y1 - 10 > text_h else y1 + text_h + 10

            cv2.rectangle(
                annotated_img,
                (text_x, text_y - text_h - baseline),
                (text_x + text_w, text_y + baseline),
                (0, 0, 0),
                thickness=cv2.FILLED,
            )
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
    crop_bg[border_thickness:-border_thickness, border_thickness:-border_thickness] = \
        crop_img_padded[border_thickness:-border_thickness, border_thickness:-border_thickness]

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
        panel = cv2.copyMakeBorder(panel, diff // 2, diff - diff // 2, 0, 0, cv2.BORDER_CONSTANT, value=base_color)
    elif panel.shape[0] > crop_bg.shape[0]:
        diff = panel.shape[0] - crop_bg.shape[0]
        crop_bg = cv2.copyMakeBorder(crop_bg, diff // 2, diff - diff // 2, 0, 0, cv2.BORDER_CONSTANT, value=base_color)

    combined_img = np.hstack((crop_bg, panel))
    cv2.imwrite(save_path, combined_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

class JerawatDetectionService:
    def __init__(self, model_path):
        self.model_path = model_path
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()

        self.input_index = input_details[0]['index']
        self.output_index = output_details[0]['index']
        self.input_shape = input_details[0]['shape']
        self.input_size = (self.input_shape[2], self.input_shape[1])  # width, height
        

    def detect(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
            
        original_h, original_w = img.shape[:2]
        print(f"Original image size: {original_w}x{original_h}")

        resized_img = cv2.resize(img, self.input_size)
        input_data = resized_img / 255.0
        input_data = np.expand_dims(input_data.astype(np.float32), axis=0)

        self.interpreter.set_tensor(self.input_index, input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_index)

        detections = output_data[0]
        
        boxes = []
        scores = []
        
        detections = detections.T
        
        for detection in detections:
            x_center, y_center, width, height, confidence = detection
            
            if confidence < DETECT_CONFIDENCE:
                continue
                
            x_center_px = x_center * original_w
            y_center_px = y_center * original_h
            width_px = width * original_w
            height_px = height * original_h
            
            x1 = int(x_center_px - width_px / 2)
            y1 = int(y_center_px - height_px / 2)
            x2 = int(x_center_px + width_px / 2)
            y2 = int(y_center_px + height_px / 2)
            
            x1 = max(0, min(x1, original_w))
            y1 = max(0, min(y1, original_h))
            x2 = max(0, min(x2, original_w))
            y2 = max(0, min(y2, original_h))
            
            if x2 <= x1 or y2 <= y1:
                continue
                
            boxes.append((x1, y1, x2, y2))
            scores.append(confidence)

        print(f"Found {len(boxes)} detections before NMS")
        
        # Apply Non-Maximum Suppression
        if boxes:
            boxes, scores = non_max_suppression(boxes, scores, iou_threshold=0.5)
            print(f"Found {len(boxes)} detections after NMS")

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
    def __init__(self, deteksi_model_path, klasifikasi_model_path, class_index_path, crop_folder="results"):
        self.detector = JerawatDetectionService(deteksi_model_path)
        self.classifier = JerawatClassificationService(klasifikasi_model_path, class_index_path)
        self.crop_folder = crop_folder
        os.makedirs(self.crop_folder, exist_ok=True)

    def process(self, image_path):
        detected_boxes, img = self.detector.detect(image_path)
        img_height, img_width = img.shape[:2]

        # Buat folder baru untuk menyimpan hasil crop dan klasifikasi
        existing_folders = [name for name in os.listdir(self.crop_folder) if os.path.isdir(os.path.join(self.crop_folder, name))]
        current_time = datetime.now().strftime("%d-%m-%Y")
        folder_index = f"{len(existing_folders)}_({current_time})"
        folder_dir = os.path.join(self.crop_folder, str(folder_index))
        
        # Buat subfolder untuk crop deteksi
        crop_dir = os.path.join(folder_dir, "deteksi_crop")
        os.makedirs(crop_dir, exist_ok=True)
        
        # Buat subfolder untuk klasifikasi
        classify_dir = os.path.join(folder_dir, "klasifikasi")
        os.makedirs(classify_dir, exist_ok=True)

        # Buat folder baru
        os.makedirs(folder_dir, exist_ok=True)
        if not detected_boxes:
            return {"message": "jerawat tidak ditemukan"}

        results = {}
        # os.makedirs("hasil_klasifikasi", exist_ok=True)

        for i, (x1, y1, x2, y2) in enumerate(detected_boxes):
            # Enlarge bounding box
            x1_enlarged, y1_enlarged, x2_enlarged, y2_enlarged = enlarge_bbox(
                x1, y1, x2, y2, ENLARGE_SCALE, img_width, img_height
            )

            # Crop the region
            crop = img[y1_enlarged:y2_enlarged, x1_enlarged:x2_enlarged]
            
            # Resize crop for better visibility
            resized_crop = cv2.resize(crop, None, fx=CROP_SCALE_FACTOR, fy=CROP_SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)
            crop_path = f"{crop_dir}/crop_{i}.jpg"
            cv2.imwrite(crop_path, resized_crop)

            # Classify the cropped region
            prediction = self.classifier.predict(crop_path)
            
            # Only include results with sufficient classification confidence
            if prediction["confidence"] >= CLASSIFY_CONFIDENCE:
                results[os.path.basename(crop_path)] = prediction

                # Create classification visualization
                save_path = f"{classify_dir}/crop_{i}.jpg"
                create_classification_image(resized_crop, prediction["class"], prediction["confidence"], save_path)

        # Create annotated image
        annotate_image_with_predictions(img, detected_boxes, results, f"{classify_dir}/annotated_image.jpg")
        return results

if __name__ == "__main__":
    pipeline = JerawatPipeline(
        deteksi_model_path="model/deteksi/best_float32.tflite",  # path TFLite baru
        klasifikasi_model_path="model/klasifikasi/model.tflite",
        class_index_path="class_indices.json"
    )

    result = pipeline.process("images.jpg")
    print(json.dumps(result, indent=4))