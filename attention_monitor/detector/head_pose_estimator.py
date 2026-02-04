"""
Head pose estimation using 3D face model and solvePnP
"""
import cv2
import numpy as np
import logging
from typing import Optional, Tuple

from ..config import HEAD_POSE_YAW_THRESHOLD, HEAD_POSE_PITCH_THRESHOLD

logger = logging.getLogger(__name__)


class HeadPoseEstimator:
    """Estimate head pose angles from face landmarks"""

    def __init__(self):
        """Initialize 3D face model"""
        # 3D model points (in cm, arbitrary scale)
        # Based on average human face proportions
        self.model_points = np.array([
            (0.0, 0.0, 0.0),          # Nose tip (index 1)
            (0.0, -6.0, -1.5),        # Chin (index 152)
            (-4.0, 3.0, -2.0),        # Left eye left corner (index 33)
            (4.0, 3.0, -2.0),         # Right eye right corner (index 263)
            (-3.0, -3.0, -2.0),       # Left mouth corner (index 61)
            (3.0, -3.0, -2.0),        # Right mouth corner (index 291)
        ], dtype=np.float64)

        # Corresponding landmark indices in MediaPipe Face Mesh
        self.landmark_indices = [1, 152, 33, 263, 61, 291]

        logger.info("HeadPoseEstimator initialized")

    def estimate(
        self, landmarks: np.ndarray, frame_shape: Tuple[int, int]
    ) -> Optional[Tuple[float, float, float]]:
        """
        Estimate head pose angles

        Args:
            landmarks: Face landmarks array (478, 3)
            frame_shape: (height, width) of the frame

        Returns:
            (yaw, pitch, roll) angles in degrees, or None if estimation fails
        """
        if landmarks is None or len(landmarks) < max(self.landmark_indices) + 1:
            return None

        h, w = frame_shape[:2]

        # Extract 2D image points
        image_points = np.array([
            landmarks[idx][:2] for idx in self.landmark_indices
        ], dtype=np.float64)

        # Camera matrix (assuming centered principal point)
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)

        # Assume no lens distortion
        dist_coeffs = np.zeros((4, 1))

        # Solve PnP to get rotation and translation vectors
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.model_points,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return None

        # Convert rotation vector to rotation matrix
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

        # Extract Euler angles from rotation matrix
        # Using the formula from: https://www.learnopencv.com/head-pose-estimation-using-opencv-and-dlib/
        sy = np.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            pitch = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
            yaw = np.arctan2(-rotation_matrix[2, 0], sy)
            roll = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
        else:
            pitch = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
            yaw = np.arctan2(-rotation_matrix[2, 0], sy)
            roll = 0

        # Convert radians to degrees
        pitch = np.degrees(pitch)
        yaw = np.degrees(yaw)
        roll = np.degrees(roll)

        # Adjust pitch home position to 0° (looking straight at screen)
        # Subtract 180° to recenter from ~180° to ~0°
        pitch = pitch - 180.0

        # Normalize pitch to -180 to 180 range
        if pitch < -180:
            pitch += 360
        elif pitch > 180:
            pitch -= 360

        return yaw, pitch, roll

    def is_looking_away(
        self, landmarks: np.ndarray, frame_shape: Tuple[int, int]
    ) -> Tuple[bool, Optional[Tuple[float, float, float]]]:
        """
        Check if head is turned away based on pose angles

        Args:
            landmarks: Face landmarks array
            frame_shape: (height, width) of the frame

        Returns:
            (is_away, angles) where angles is (yaw, pitch, roll) or None
        """
        angles = self.estimate(landmarks, frame_shape)

        if angles is None:
            return False, None

        yaw, pitch, roll = angles

        # Check if head is turned beyond thresholds
        is_away = (
            abs(yaw) > HEAD_POSE_YAW_THRESHOLD or
            abs(pitch) > HEAD_POSE_PITCH_THRESHOLD
        )

        return is_away, angles

    def draw_pose(
        self,
        frame: np.ndarray,
        landmarks: np.ndarray,
        angles: Optional[Tuple[float, float, float]] = None
    ) -> np.ndarray:
        """
        Draw head pose visualization on frame

        Args:
            frame: BGR image
            landmarks: Face landmarks array
            angles: Pre-computed angles or None to compute

        Returns:
            Frame with pose visualization
        """
        if landmarks is None:
            return frame

        if angles is None:
            angles = self.estimate(landmarks, frame.shape[:2])

        if angles is None:
            return frame

        yaw, pitch, roll = angles
        annotated_frame = frame.copy()

        # Draw text with angles
        text = f"Yaw: {yaw:.1f}, Pitch: {pitch:.1f}, Roll: {roll:.1f}"
        cv2.putText(
            annotated_frame,
            text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        # Optionally draw axis (nose tip as origin)
        nose_tip = landmarks[1][:2].astype(int)

        # Draw a simple indicator at nose
        cv2.circle(annotated_frame, tuple(nose_tip), 5, (0, 0, 255), -1)

        return annotated_frame
