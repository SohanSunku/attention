"""
Face detection using MediaPipe Face Mesh
"""
import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Optional

from ..config import (
    MEDIAPIPE_MAX_FACES,
    MEDIAPIPE_REFINE_LANDMARKS,
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
)

logger = logging.getLogger(__name__)


class FaceDetector:
    """Detect face and extract landmarks using MediaPipe"""

    def __init__(self):
        """Initialize MediaPipe Face Mesh"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=MEDIAPIPE_MAX_FACES,
            refine_landmarks=MEDIAPIPE_REFINE_LANDMARKS,
            min_detection_confidence=MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
        )
        logger.info("FaceDetector initialized")

    def detect(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect face and extract landmarks

        Args:
            frame: BGR image from camera

        Returns:
            Array of landmarks with shape (478, 3) containing (x, y, z) coordinates
            normalized to image dimensions, or None if no face detected
        """
        if frame is None:
            return None

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None

        # Extract landmarks from first face
        face_landmarks = results.multi_face_landmarks[0]

        # Convert to numpy array with image coordinates
        h, w = frame.shape[:2]
        landmarks = np.array([
            [lm.x * w, lm.y * h, lm.z * w]  # z is also scaled by width
            for lm in face_landmarks.landmark
        ])

        return landmarks

    def draw_landmarks(self, frame: np.ndarray, landmarks: Optional[np.ndarray]) -> np.ndarray:
        """
        Draw face landmarks on frame for debugging

        Args:
            frame: BGR image
            landmarks: Landmarks array from detect()

        Returns:
            Frame with landmarks drawn
        """
        if landmarks is None:
            return frame

        annotated_frame = frame.copy()

        # Draw face mesh points (first 468 landmarks)
        for i in range(min(468, len(landmarks))):
            x, y = int(landmarks[i][0]), int(landmarks[i][1])
            cv2.circle(annotated_frame, (x, y), 1, (0, 255, 0), -1)

        # Draw iris landmarks in different color (468-477 for left, 473-482 for right)
        iris_indices = list(range(468, 478))
        for i in iris_indices:
            if i < len(landmarks):
                x, y = int(landmarks[i][0]), int(landmarks[i][1])
                cv2.circle(annotated_frame, (x, y), 2, (255, 0, 0), -1)

        return annotated_frame

    def close(self):
        """Release resources"""
        if self.face_mesh:
            self.face_mesh.close()
            logger.info("FaceDetector closed")

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
