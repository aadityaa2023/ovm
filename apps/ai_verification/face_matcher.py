import cv2
import numpy as np
from typing import Tuple, Optional
import pickle


class FaceMatcher:
    """Face recognition and matching using feature extraction"""
    
    def __init__(self):
        # Using ORB (Oriented FAST and Rotated BRIEF) for feature detection
        # This is faster than deep learning models and works without GPU
        self.orb = cv2.ORB_create(nfeatures=500)
        self.bf_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Alternative: Use face_recognition library if available
        self.use_face_recognition = False
        try:
            import face_recognition
            self.face_recognition = face_recognition
            self.use_face_recognition = True
        except ImportError:
            pass
    
    def extract_face_encoding(self, face_image: np.ndarray) -> Optional[bytes]:
        """
        Extract face encoding/features from face image
        
        Args:
            face_image: numpy array of face region
            
        Returns:
            Serialized face encoding as bytes
        """
        if self.use_face_recognition:
            return self._extract_encoding_face_recognition(face_image)
        else:
            return self._extract_encoding_orb(face_image)
    
    def _extract_encoding_face_recognition(self, face_image: np.ndarray) -> Optional[bytes]:
        """Extract encoding using face_recognition library"""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Get face encodings
            encodings = self.face_recognition.face_encodings(rgb_image)
            
            if len(encodings) == 0:
                return None
            
            # Serialize the encoding
            encoding_bytes = pickle.dumps(encodings[0])
            return encoding_bytes
        except Exception as e:
            print(f"Error extracting face encoding: {e}")
            return None
    
    def _extract_encoding_orb(self, face_image: np.ndarray) -> Optional[bytes]:
        """Extract features using ORB"""
        try:
            # Resize to standard size
            face_resized = cv2.resize(face_image, (128, 128))
            gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
            
            # Detect keypoints and compute descriptors
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            if descriptors is None:
                return None
            
            # Serialize descriptors
            encoding_bytes = pickle.dumps(descriptors)
            return encoding_bytes
        except Exception as e:
            print(f"Error extracting ORB features: {e}")
            return None
    
    def compare_faces(self, encoding1: bytes, encoding2: bytes) -> Tuple[bool, float]:
        """
        Compare two face encodings
        
        Args:
            encoding1: First face encoding (bytes)
            encoding2: Second face encoding (bytes)
            
        Returns:
            (is_match, confidence_score)
        """
        if self.use_face_recognition:
            return self._compare_face_recognition(encoding1, encoding2)
        else:
            return self._compare_orb(encoding1, encoding2)
    
    def _compare_face_recognition(self, encoding1: bytes, encoding2: bytes) -> Tuple[bool, float]:
        """Compare using face_recognition library"""
        try:
            # Deserialize encodings
            enc1 = pickle.loads(encoding1)
            enc2 = pickle.loads(encoding2)
            
            # Calculate face distance
            distance = self.face_recognition.face_distance([enc1], enc2)[0]
            
            # Convert distance to similarity (0-1 scale)
            similarity = 1 - distance
            
            # Threshold for match
            is_match = distance < 0.6  # Standard threshold
            
            return is_match, float(similarity)
        except Exception as e:
            print(f"Error comparing faces: {e}")
            return False, 0.0
    
    def _compare_orb(self, encoding1: bytes, encoding2: bytes) -> Tuple[bool, float]:
        """Compare using ORB descriptors"""
        try:
            # Deserialize descriptors
            desc1 = pickle.loads(encoding1)
            desc2 = pickle.loads(encoding2)
            
            # Match descriptors
            matches = self.bf_matcher.match(desc1, desc2)
            
            # Sort matches by distance
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Calculate similarity based on good matches
            good_matches = [m for m in matches if m.distance < 50]
            similarity = len(good_matches) / max(len(desc1), len(desc2))
            
            # Threshold for match
            is_match = similarity > 0.3
            
            return is_match, float(similarity)
        except Exception as e:
            print(f"Error comparing ORB features: {e}")
            return False, 0.0
    
    def find_duplicate_in_database(self, new_encoding: bytes, existing_encodings: list) -> Tuple[bool, Optional[int], float]:
        """
        Check if face matches any existing face in database
        
        Args:
            new_encoding: Face encoding to check
            existing_encodings: List of (voter_id, encoding) tuples
            
        Returns:
            (duplicate_found, matching_voter_id, confidence)
        """
        best_match_id = None
        best_confidence = 0.0
        
        for voter_id, existing_encoding in existing_encodings:
            if existing_encoding is None:
                continue
            
            is_match, confidence = self.compare_faces(new_encoding, existing_encoding)
            
            if is_match and confidence > best_confidence:
                best_confidence = confidence
                best_match_id = voter_id
        
        duplicate_found = best_match_id is not None
        
        return duplicate_found, best_match_id, best_confidence
