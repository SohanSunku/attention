"""
Gaze estimation using iris position and eye aspect ratio
"""
import numpy as np
import logging
from typing import Optional, Tuple

from ..config import (
    EYE_ASPECT_RATIO_THRESHOLD,
    GAZE_CENTER_MIN,
    GAZE_CENTER_MAX,
    GAZE_AWAY_THRESHOLD,
)

logger = logging.getLogger(__name__)


class GazeEstimator:
    """Estimate gaze direction from eye landmarks"""

    def __init__(self):
        """Initialize with MediaPipe landmark indices"""
        # Left eye landmarks (indices for eye contour)
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        # Right eye landmarks
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]

        # Iris landmarks (MediaPipe 478-point model)
        # Left iris center is average of indices 468-472
        self.LEFT_IRIS = list(range(468, 473))
        # Right iris center is average of indices 473-477
        self.RIGHT_IRIS = list(range(473, 478))

        # Eye corner landmarks
        self.LEFT_EYE_CORNERS = [33, 133]   # inner, outer
        self.RIGHT_EYE_CORNERS = [362, 263]  # inner, outer

        logger.info("GazeEstimator initialized")

    def _calculate_eye_aspect_ratio(self, eye_landmarks: np.ndarray) -> float:
        """
        Calculate Eye Aspect Ratio (EAR)
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

        Args:
            eye_landmarks: Array of 6 eye contour points

        Returns:
            EAR value
        """
        # Vertical distances
        v1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        v2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])

        # Horizontal distance
        h = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])

        # Avoid division by zero
        if h < 1e-6:
            return 0.0

        ear = (v1 + v2) / (2.0 * h)
        return ear

    def _calculate_gaze_ratio(
        self, iris_center: np.ndarray, eye_corners: np.ndarray
    ) -> float:
        """
        Calculate horizontal gaze ratio
        ratio = (iris_x - left_corner_x) / (right_corner_x - left_corner_x)

        Args:
            iris_center: (x, y) position of iris center
            eye_corners: Array of 2 corner points [inner, outer]

        Returns:
            Gaze ratio (0.0 = looking far left, 1.0 = looking far right, 0.5 = center)
        """
        left_corner = eye_corners[0]
        right_corner = eye_corners[1]

        # Use x-coordinates only
        iris_x = iris_center[0]
        left_x = left_corner[0]
        right_x = right_corner[0]

        # Ensure left is actually left
        if left_x > right_x:
            left_x, right_x = right_x, left_x

        width = right_x - left_x
        if width < 1e-6:
            return 0.5  # Default to center if width is too small

        ratio = (iris_x - left_x) / width
        return np.clip(ratio, 0.0, 1.0)

    def estimate(self, landmarks: np.ndarray) -> Optional[dict]:
        """
        Estimate gaze direction and eye state

        Args:
            landmarks: Face landmarks array (478, 3)

        Returns:
            Dictionary with gaze information or None if estimation fails
            {
                'left_ear': float,
                'right_ear': float,
                'left_gaze': float,
                'right_gaze': float,
                'eyes_closed': bool,
                'looking_away': bool,
            }
        """
        if landmarks is None or len(landmarks) < 478:
            return None

        try:
            # Get eye landmarks
            left_eye_points = landmarks[self.LEFT_EYE]
            right_eye_points = landmarks[self.RIGHT_EYE]

            # Calculate EAR for both eyes
            left_ear = self._calculate_eye_aspect_ratio(left_eye_points)
            right_ear = self._calculate_eye_aspect_ratio(right_eye_points)

            # Check if eyes are closed
            eyes_closed = (
                left_ear < EYE_ASPECT_RATIO_THRESHOLD and
                right_ear < EYE_ASPECT_RATIO_THRESHOLD
            )

            # Calculate iris centers
            left_iris_points = landmarks[self.LEFT_IRIS]
            right_iris_points = landmarks[self.RIGHT_IRIS]

            left_iris_center = np.mean(left_iris_points, axis=0)[:2]
            right_iris_center = np.mean(right_iris_points, axis=0)[:2]

            # Get eye corners
            left_corners = landmarks[self.LEFT_EYE_CORNERS]
            right_corners = landmarks[self.RIGHT_EYE_CORNERS]

            # Calculate gaze ratios
            left_gaze = self._calculate_gaze_ratio(left_iris_center, left_corners)
            right_gaze = self._calculate_gaze_ratio(right_iris_center, right_corners)

            # Check if looking away (gaze outside center range)
            looking_away = (
                left_gaze < GAZE_AWAY_THRESHOLD or
                left_gaze > (1.0 - GAZE_AWAY_THRESHOLD) or
                right_gaze < GAZE_AWAY_THRESHOLD or
                right_gaze > (1.0 - GAZE_AWAY_THRESHOLD)
            )

            return {
                'left_ear': left_ear,
                'right_ear': right_ear,
                'left_gaze': left_gaze,
                'right_gaze': right_gaze,
                'eyes_closed': eyes_closed,
                'looking_away': looking_away,
            }

        except Exception as e:
            logger.warning(f"Gaze estimation error: {e}")
            return None

    def draw_gaze(
        self, frame: np.ndarray, landmarks: np.ndarray, gaze_info: Optional[dict] = None
    ) -> np.ndarray:
        """
        Draw gaze information on frame

        Args:
            frame: BGR image
            landmarks: Face landmarks array
            gaze_info: Pre-computed gaze info or None to compute

        Returns:
            Frame with gaze visualization
        """
        if landmarks is None:
            return frame

        if gaze_info is None:
            gaze_info = self.estimate(landmarks)

        if gaze_info is None:
            return frame

        annotated_frame = frame.copy()

        # Draw text with gaze information
        y_offset = 60
        cv2.putText(
            annotated_frame,
            f"Left Gaze: {gaze_info['left_gaze']:.2f}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        y_offset += 25
        cv2.putText(
            annotated_frame,
            f"Right Gaze: {gaze_info['right_gaze']:.2f}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        y_offset += 25
        cv2.putText(
            annotated_frame,
            f"Left EAR: {gaze_info['left_ear']:.2f}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        y_offset += 25
        cv2.putText(
            annotated_frame,
            f"Right EAR: {gaze_info['right_ear']:.2f}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        return annotated_frame
