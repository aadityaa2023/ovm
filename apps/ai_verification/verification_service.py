from .face_detector import FaceDetector
from .liveness_detector import LivenessDetector
from .face_matcher import FaceMatcher
from typing import Dict, Optional, Tuple
import numpy as np


class VerificationService:
    """Main service for voter identity verification"""
    
    def __init__(self):
        self.face_detector = FaceDetector()
        self.liveness_detector = LivenessDetector()
        self.face_matcher = FaceMatcher()
    
    def verify_registration(self, image_base64: str, existing_encodings: list = None) -> Dict:
        """
        Verify voter during registration
        
        Args:
            image_base64: Base64 encoded image from webcam
            existing_encodings: List of (voter_id, encoding) tuples for duplicate check
            
        Returns:
            dict with verification results
        """
        result = {
            'success': False,
            'face_detected': False,
            'face_encoding': None,
            'duplicate_found': False,
            'duplicate_voter_id': None,
            'confidence': 0.0,
            'message': ''
        }
        
        # Process image
        image_array = self.face_detector.process_base64_image(image_base64)
        if image_array is None:
            result['message'] = 'Failed to process image'
            return result
        
        # Validate image quality
        is_valid, quality_message = self.face_detector.validate_image_quality(image_array)
        if not is_valid:
            result['message'] = quality_message
            return result
        
        # Detect face
        face_detected, coordinates, detection_confidence = self.face_detector.detect_face(image_array)
        result['face_detected'] = face_detected
        
        if not face_detected:
            result['message'] = 'No face detected or multiple faces in frame'
            return result
        
        # Extract face region
        face_region = self.face_detector.extract_face_region(image_array, coordinates)
        
        # Extract face encoding
        face_encoding = self.face_matcher.extract_face_encoding(face_region)
        if face_encoding is None:
            result['message'] = 'Failed to extract face features'
            return result
        
        result['face_encoding'] = face_encoding
        
        # Check for duplicates
        if existing_encodings:
            duplicate_found, duplicate_id, dup_confidence = self.face_matcher.find_duplicate_in_database(
                face_encoding, existing_encodings
            )
            result['duplicate_found'] = duplicate_found
            result['duplicate_voter_id'] = duplicate_id
            
            if duplicate_found:
                result['message'] = f'Duplicate registration detected (Confidence: {dup_confidence:.2f})'
                result['confidence'] = dup_confidence
                return result
        
        # Success
        result['success'] = True
        result['confidence'] = detection_confidence
        result['message'] = 'Face verified successfully'
        
        return result
    
    def verify_login(self, image_base64: str, stored_encoding: bytes, require_liveness: bool = True) -> Dict:
        """
        Verify voter during login
        
        Args:
            image_base64: Base64 encoded image from webcam
            stored_encoding: Stored face encoding from database
            require_liveness: Whether to perform liveness check
            
        Returns:
            dict with verification results
        """
        result = {
            'success': False,
            'face_matched': False,
            'liveness_passed': False,
            'confidence': 0.0,
            'message': ''
        }
        
        # Process image
        image_array = self.face_detector.process_base64_image(image_base64)
        if image_array is None:
            result['message'] = 'Failed to process image'
            return result
        
        # Detect face
        face_detected, coordinates, _ = self.face_detector.detect_face(image_array)
        if not face_detected:
            result['message'] = 'No face detected'
            return result
        
        # Extract face region
        face_region = self.face_detector.extract_face_region(image_array, coordinates)
        
        # Extract face encoding
        current_encoding = self.face_matcher.extract_face_encoding(face_region)
        if current_encoding is None:
            result['message'] = 'Failed to extract face features'
            return result
        
        # Compare with stored encoding
        is_match, match_confidence = self.face_matcher.compare_faces(current_encoding, stored_encoding)
        result['face_matched'] = is_match
        result['confidence'] = match_confidence
        
        if not is_match:
            result['message'] = f'Face does not match (Confidence: {match_confidence:.2f})'
            return result
        
        # Liveness check (optional but recommended)
        if require_liveness:
            # For single image, we can only do texture analysis
            is_live, liveness_conf = self.liveness_detector.check_texture_analysis(image_array)
            result['liveness_passed'] = is_live
            
            if not is_live:
                result['message'] = 'Liveness check failed - possible spoofing attempt'
                return result
        else:
            result['liveness_passed'] = True
        
        # Success
        result['success'] = True
        result['message'] = 'Identity verified successfully'
        
        return result
    
    def verify_liveness_video(self, frames_base64: list) -> Dict:
        """
        Perform liveness check on video frames
        
        Args:
            frames_base64: List of base64 encoded frames
            
        Returns:
            dict with liveness results
        """
        result = {
            'success': False,
            'is_live': False,
            'confidence': 0.0,
            'checks': {},
            'message': ''
        }
        
        # Convert frames
        frames = []
        for frame_b64 in frames_base64:
            frame_array = self.face_detector.process_base64_image(frame_b64)
            if frame_array is not None:
                frames.append(frame_array)
        
        if len(frames) < 3:
            result['message'] = 'Insufficient frames for liveness detection'
            return result
        
        # Perform liveness check
        liveness_result = self.liveness_detector.perform_liveness_check(frames)
        
        result['success'] = True
        result['is_live'] = liveness_result['is_live']
        result['confidence'] = liveness_result['confidence']
        result['checks'] = liveness_result['checks']
        result['message'] = 'Liveness check completed'
        
        return result


# Singleton instance
verification_service = VerificationService()
