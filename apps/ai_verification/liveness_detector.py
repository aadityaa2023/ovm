import cv2
import numpy as np
from typing import Tuple
import time


class LivenessDetector:
    """Detect if the face is from a live person (anti-spoofing)"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        
        # Blink detection parameters
        self.blink_threshold = 0.2
        self.consecutive_frames = 3
    
    def detect_blink(self, frames: list) -> Tuple[bool, float]:
        """
        Detect blink in a sequence of frames
        
        Args:
            frames: List of image frames (numpy arrays)
            
        Returns:
            (blink_detected, confidence)
        """
        if len(frames) < 5:
            return False, 0.0
        
        eye_states = []
        
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                continue
            
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                eye_states.append(len(eyes))
        
        if len(eye_states) < 3:
            return False, 0.0
        
        # Check for eye state changes (blink pattern)
        blink_detected = False
        for i in range(len(eye_states) - 2):
            # Pattern: eyes open -> closed -> open
            if eye_states[i] >= 2 and eye_states[i+1] < 2 and eye_states[i+2] >= 2:
                blink_detected = True
                break
        
        confidence = 0.9 if blink_detected else 0.3
        return blink_detected, confidence
    
    def detect_head_movement(self, frames: list) -> Tuple[bool, float]:
        """
        Detect head movement across frames
        
        Args:
            frames: List of image frames
            
        Returns:
            (movement_detected, confidence)
        """
        if len(frames) < 3:
            return False, 0.0
        
        face_positions = []
        
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                center_x = x + w // 2
                center_y = y + h // 2
                face_positions.append((center_x, center_y))
        
        if len(face_positions) < 3:
            return False, 0.0
        
        # Calculate movement
        movements = []
        for i in range(len(face_positions) - 1):
            x1, y1 = face_positions[i]
            x2, y2 = face_positions[i + 1]
            distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            movements.append(distance)
        
        avg_movement = np.mean(movements)
        
        # Movement should be noticeable but not too much (to avoid false positives)
        movement_detected = 10 < avg_movement < 100
        confidence = min(0.95, avg_movement / 50) if movement_detected else 0.2
        
        return movement_detected, confidence
    
    def check_texture_analysis(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Analyze image texture to detect printed photos or screens
        
        Args:
            image: Single image frame
            
        Returns:
            (is_live, confidence)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate Local Binary Pattern variance
        # Real faces have more texture variation than printed photos
        
        # Simple texture analysis using Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # Real faces typically have variance > 500
        is_live = variance > 500
        confidence = min(0.9, variance / 1000) if is_live else 0.3
        
        return is_live, confidence
    
    def perform_liveness_check(self, frames: list) -> dict:
        """
        Perform comprehensive liveness check
        
        Args:
            frames: List of sequential frames from video
            
        Returns:
            dict with liveness results
        """
        results = {
            'is_live': False,
            'confidence': 0.0,
            'checks': {}
        }
        
        # Blink detection
        blink_detected, blink_conf = self.detect_blink(frames)
        results['checks']['blink'] = {
            'passed': blink_detected,
            'confidence': blink_conf
        }
        
        # Head movement
        movement_detected, movement_conf = self.detect_head_movement(frames)
        results['checks']['movement'] = {
            'passed': movement_detected,
            'confidence': movement_conf
        }
        
        # Texture analysis on last frame
        if len(frames) > 0:
            texture_live, texture_conf = self.check_texture_analysis(frames[-1])
            results['checks']['texture'] = {
                'passed': texture_live,
                'confidence': texture_conf
            }
        
        # Overall decision: at least 2 checks should pass
        passed_checks = sum([
            results['checks'].get('blink', {}).get('passed', False),
            results['checks'].get('movement', {}).get('passed', False),
            results['checks'].get('texture', {}).get('passed', False)
        ])
        
        results['is_live'] = passed_checks >= 2
        
        # Calculate overall confidence
        confidences = [
            results['checks'].get('blink', {}).get('confidence', 0),
            results['checks'].get('movement', {}).get('confidence', 0),
            results['checks'].get('texture', {}).get('confidence', 0)
        ]
        results['confidence'] = np.mean(confidences)
        
        return results
