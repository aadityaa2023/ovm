import cv2
import numpy as np
from typing import Tuple, Optional
import base64
from io import BytesIO
from PIL import Image


class FaceDetector:
    """Face detection using OpenCV Haar Cascades"""
    
    def __init__(self):
        # Load pre-trained Haar Cascade classifier
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def detect_face(self, image_data: np.ndarray) -> Tuple[bool, Optional[Tuple], float]:
        """
        Detect face in image
        
        Args:
            image_data: numpy array of image
            
        Returns:
            (face_detected, face_coordinates, confidence)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            return False, None, 0.0
        
        if len(faces) > 1:
            # Multiple faces detected
            return False, None, 0.0
        
        # Single face detected
        x, y, w, h = faces[0]
        
        # Detect eyes for additional validation
        roi_gray = gray[y:y+h, x:x+w]
        eyes = self.eye_cascade.detectMultiScale(roi_gray)
        
        # Confidence based on eye detection
        confidence = 0.8 if len(eyes) >= 2 else 0.6
        
        return True, (x, y, w, h), confidence
    
    def extract_face_region(self, image_data: np.ndarray, coordinates: Tuple) -> np.ndarray:
        """Extract face region from image"""
        x, y, w, h = coordinates
        # Add some padding
        padding = 20
        x_start = max(0, x - padding)
        y_start = max(0, y - padding)
        x_end = min(image_data.shape[1], x + w + padding)
        y_end = min(image_data.shape[0], y + h + padding)
        
        face_region = image_data[y_start:y_end, x_start:x_end]
        return face_region
    
    def process_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Convert base64 string to numpy array"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            return image_array
        except Exception as e:
            print(f"Error processing base64 image: {e}")
            return None
    
    def validate_image_quality(self, image_data: np.ndarray) -> Tuple[bool, str]:
        """
        Validate image quality for face recognition
        
        Returns:
            (is_valid, message)
        """
        # Check image size
        height, width = image_data.shape[:2]
        if width < 200 or height < 200:
            return False, "Image resolution too low"
        
        # Check brightness
        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 50:
            return False, "Image too dark"
        if mean_brightness > 200:
            return False, "Image too bright"
        
        # Check blur
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:
            return False, "Image too blurry"
        
        return True, "Image quality acceptable"
