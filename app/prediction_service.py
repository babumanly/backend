# app/prediction_service.py
import os
import json
import io
import numpy as np
from PIL import Image
import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "plant_disease_model.tflite")
CLASS_PATH = os.path.join(BASE_DIR, "..", "models", "class_indices.json")

# Load class indices
with open(CLASS_PATH, "r") as f:
    class_indices = json.load(f)

# Convert keys to int
index_to_class = {int(k): v for k, v in class_indices.items()}

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_image(image_bytes: bytes, target_size=(224, 224)) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(target_size)

    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    return img_array.astype(np.float32)

def predict_disease(image_bytes: bytes) -> dict:
    processed_img = preprocess_image(image_bytes)

    interpreter.set_tensor(input_details[0]['index'], processed_img)
    interpreter.invoke()

    prediction = interpreter.get_tensor(output_details[0]['index'])

    predicted_class_index = int(np.argmax(prediction, axis=1)[0])
    disease_name = index_to_class.get(predicted_class_index, "Unknown Disease")
    confidence = float(np.max(prediction))

    return {
        "disease_name": disease_name,
        "confidence": confidence
    }
