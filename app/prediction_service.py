# app/prediction_service.py
import os
import json
import io
import numpy as np
from PIL import Image

# -----------------------------------------------------------
# LIGHTWEIGHT MODEL LOADING (Fixes Render 503 / Out of Memory)
# -----------------------------------------------------------
try:
    # Try loading lightweight runtime (Best for Render/Linux)
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        # Fallback for Local Dev if tflite-runtime isn't installed
        import tensorflow.lite as tflite
    except ImportError:
        # Last resort (Heavy, but works locally)
        import tensorflow as tf
        tflite = tf.lite

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "plant_disease_model.tflite")
CLASS_PATH = os.path.join(BASE_DIR, "..", "models", "class_indices.json")

# Load class indices
with open(CLASS_PATH, "r") as f:
    class_indices = json.load(f)

# Convert keys to int
index_to_class = {int(k): v for k, v in class_indices.items()}

# Load TFLite model
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_image(image_bytes: bytes, target_size=(224, 224)) -> np.ndarray:
    """
    Process image using pure NumPy/PIL to save memory.
    Replaces heavy tf.keras.preprocessing.image.img_to_array
    """
    # 1. Open Image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # 2. Resize (using PIL instead of TF)
    img = img.resize(target_size, Image.Resampling.NEAREST)

    # 3. Convert to Array (using NumPy)
    img_array = np.array(img, dtype=np.float32)
    
    # 4. Normalize
    img_array = img_array / 255.0
    
    # 5. Expand Dimensions (H, W, C) -> (1, H, W, C)
    img_array = np.expand_dims(img_array, axis=0)

    return img_array

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
