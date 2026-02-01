import numpy as np
import cv2

def analyze_severity(image_bytes: bytes) -> float:
    """
    Analyzes the severity of the plant disease from an image using color segmentation.
    Returns the severity as a percentage.
    """
    # Convert bytes to an OpenCV image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Convert the image from BGR to HSV color space
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # --- IMPORTANT: TUNING REQUIRED ---
    # These HSV color ranges are examples and will need to be carefully tuned 
    # for the specific types of leaves and diseases in your dataset.
    
    # Define HSV range for HEALTHY green parts of a leaf
    lower_green = np.array([25, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    # Define HSV range for DISEASED parts (e.g., brown/yellow spots)
    # You might need multiple ranges and combine the masks
    lower_disease = np.array([10, 80, 80])
    upper_disease = np.array([30, 255, 255])

    # Create masks to isolate healthy and diseased pixels
    healthy_mask = cv2.inRange(hsv_img, lower_green, upper_green)
    disease_mask = cv2.inRange(hsv_img, lower_disease, upper_disease)
    
    # Calculate the number of pixels for each category
    healthy_pixels = cv2.countNonZero(healthy_mask)
    disease_pixels = cv2.countNonZero(disease_mask)

    # Calculate severity percentage based on visible leaf area
    total_leaf_pixels = healthy_pixels + disease_pixels
    
    if total_leaf_pixels == 0:
        return 0.0  # Avoid division by zero if no leaf is detected

    severity_percentage = (disease_pixels / total_leaf_pixels) * 100
    
    return severity_percentage