"""
Attention state analysis combining multiple detection signals
"""
import logging
from enum import Enum
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class AttentionState(Enum):
    """Possible attention states"""
    FOCUSED = "focused"         # User is looking at screen
    DISTRACTED = "distracted"   # User is present but not looking at screen
    AWAY = "away"               # User's head is turned away
    UNKNOWN = "unknown"         # Cannot determine (no face detected)


class AttentionAnalyzer:
    """Analyze attention state from multiple signals"""

    def __init__(self):
        """Initialize analyzer"""
        logger.info("AttentionAnalyzer initialized")

    def analyze(
        self,
        landmarks: Optional[np.ndarray],
        head_pose_angles: Optional[Tuple[float, float, float]],
        gaze_info: Optional[dict],
    ) -> Tuple[AttentionState, float]:
        """
        Determine attention state from multiple signals

        Decision hierarchy:
        1. No face detected → UNKNOWN
        2. EAR < threshold (both eyes) → DISTRACTED (eyes closed)
        3. |yaw| > 30° OR |pitch| > 20° → AWAY (head turned)
        4. gaze < 0.30 OR gaze > 0.70 → DISTRACTED (looking elsewhere)
        5. Otherwise → FOCUSED

        Args:
            landmarks: Face landmarks array or None
            head_pose_angles: (yaw, pitch, roll) or None
            gaze_info: Gaze estimation dict or None

        Returns:
            (AttentionState, confidence_score) where confidence is 0.0-1.0
        """
        # 1. No face detected
        if landmarks is None:
            return AttentionState.UNKNOWN, 0.0

        # Initialize confidence and state
        confidence = 1.0
        state = AttentionState.FOCUSED

        # 2. Check if eyes are closed
        if gaze_info is not None and gaze_info.get('eyes_closed', False):
            return AttentionState.DISTRACTED, 0.9

        # 3. Check head pose
        if head_pose_angles is not None:
            yaw, pitch, roll = head_pose_angles

            # Head turned significantly away
            if abs(yaw) > 30 or abs(pitch) > 20:
                return AttentionState.AWAY, 0.95

            # Moderate head turn reduces confidence but still focused
            if abs(yaw) > 20 or abs(pitch) > 15:
                confidence *= 0.7
                state = AttentionState.DISTRACTED

        # 4. Check gaze direction
        if gaze_info is not None:
            left_gaze = gaze_info.get('left_gaze', 0.5)
            right_gaze = gaze_info.get('right_gaze', 0.5)

            # Average gaze position
            avg_gaze = (left_gaze + right_gaze) / 2.0

            # Definite look away
            if avg_gaze < 0.30 or avg_gaze > 0.70:
                return AttentionState.DISTRACTED, 0.85

            # Slight gaze away reduces confidence
            if avg_gaze < 0.35 or avg_gaze > 0.65:
                confidence *= 0.8
                if state == AttentionState.FOCUSED:
                    state = AttentionState.DISTRACTED

        # 5. Return final state
        return state, confidence

    def state_to_string(self, state: AttentionState) -> str:
        """Convert state to display string"""
        return state.value.upper()

    def get_state_color(self, state: AttentionState) -> Tuple[int, int, int]:
        """
        Get BGR color for state visualization

        Returns:
            (B, G, R) tuple
        """
        color_map = {
            AttentionState.FOCUSED: (0, 255, 0),      # Green
            AttentionState.DISTRACTED: (0, 255, 255), # Yellow
            AttentionState.AWAY: (0, 0, 255),         # Red
            AttentionState.UNKNOWN: (128, 128, 128),  # Gray
        }
        return color_map.get(state, (255, 255, 255))
