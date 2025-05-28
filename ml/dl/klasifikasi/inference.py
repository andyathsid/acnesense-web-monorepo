import os
import json
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import load_img, img_to_array

DETEKSI_TFLITE_PATH = "tflite/deteksi/best_float32.tflite"
KLASIFIKASI_TFLITE_PATH = "tflite/klasifikasi/model.tflite"
IMAGE_PATH = "papular.jpg"
CROP_FOLDER = "hasil_crop"
CLASS_INDEX_PATH = "class_indices.json"
YOLO_CONFIDENCE = 0.65
ENLARGE_SCALE = 1.75
CROP_SCALE_FACTOR = 4.5
TARGET_IMG_SIZE = (128, 128)

# Membuat bounding box yang diperbesar
def enlarge_bbox(x1, y1, x2, y2, scale, img_width, img_height):
    w, h = x2 - x1, y2 - y1
    cx, cy = x1 + w / 2, y1 + h / 2
    new_w, new_h = w * scale, h * scale
    new_x1 = max(0, int(cx - new_w / 2))
    new_y1 = max(0, int(cy - new_h / 2))
    new_x2 = min(img_width, int(cx + new_w / 2))
    new_y2 = min(img_height, int(cy + new_h / 2))
    return new_x1, new_y1, new_x2, new_y2

# Memuat dan menjalankan model TFLite YOLO
def run_yolo_tflite(tflite_model_path, image_path):
    interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_shape = input_details[0]['shape']
    img = cv2.imread(image_path)
    original_height, original_width = img.shape[:2]
    resized_img = cv2.resize(img, (input_shape[2], input_shape[1]))
    input_tensor = np.expand_dims(resized_img, axis=0).astype(np.float32) / 255.0

    interpreter.set_tensor(input_details[0]['index'], input_tensor)
    interpreter.invoke()

    # Output deteksi bisa bervariasi tergantung model YOLO yang digunakan
    # Di sini kita asumsikan model output adalah: [box, class, score]
    boxes = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0]
    scores = interpreter.get_tensor(output_details[2]['index'])[0]


    results = []
    for box, score in zip(boxes, scores):
        if score >= YOLO_CONFIDENCE:
            y1, x1, y2, x2 = box
            results.append((
                int(x1 * original_width),
                int(y1 * original_height),
                int(x2 * original_width),
                int(y2 * original_height)
            ))
    return results, img

# Menyimpan hasil crop dari deteksi
os.makedirs(CROP_FOLDER, exist_ok=True)
detected_boxes, img = run_yolo_tflite(DETEKSI_TFLITE_PATH, IMAGE_PATH)
img_height, img_width = img.shape[:2]
crop_paths = []

for i, (x1, y1, x2, y2) in enumerate(detected_boxes):
    x1, y1, x2, y2 = enlarge_bbox(x1, y1, x2, y2, ENLARGE_SCALE, img_width, img_height)
    crop = img[y1:y2, x1:x2]
    resized_crop = cv2.resize(crop, None, fx=CROP_SCALE_FACTOR, fy=CROP_SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)
    crop_path = f"{CROP_FOLDER}/crop_{i}.jpg"
    cv2.imwrite(crop_path, resized_crop)
    crop_paths.append(crop_path)

if not crop_paths:
    print(json.dumps({"message": "jerawat tidak ditemukan"}, indent=4))
    exit()

# Load class indices
with open(CLASS_INDEX_PATH, "r") as f:
    class_indices = json.load(f)
class_names = {int(v): k for k, v in class_indices.items()}

# Fungsi klasifikasi dengan TFLite
def predict_image_tflite(img_path, model_path):
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    img = load_img(img_path, target_size=TARGET_IMG_SIZE)
    img_array = img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array.astype(np.float32), axis=0)

    interpreter.set_tensor(input_details[0]['index'], img_array)
    interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])[0]
    predicted_index = np.argmax(prediction)
    predicted_label = class_names[predicted_index]
    confidence = float(prediction[predicted_index])
    return predicted_label, confidence

# Hasil klasifikasi
classification_results = {}

for path in crop_paths:
    predicted_class, confidence = predict_image_tflite(path, KLASIFIKASI_TFLITE_PATH)
    classification_results[os.path.basename(path)] = {
        "class": predicted_class,
        "confidence": round(confidence, 4)
    }

# Output JSON akhir
json_output = json.dumps(classification_results, indent=4)
print(json_output)
