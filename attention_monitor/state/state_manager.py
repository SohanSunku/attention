"""
State management with time-based transitions and hysteresis
"""
import time
import logging
from collections import deque
from typing import Tuple, Optional
from statistics import median

from ..detector.attention_analyzer import AttentionState
from ..config import (
    STATE_BUFFER_SIZE,
    AWAY_CONFIRMATION_DELAY,
    FOCUSED_RETURN_DELAY,
    DIM_THRESHOLD_1,
    DIM_LEVEL_1,
    DIM_THRESHOLD_2,
    DIM_LEVEL_2,
    DISPLAY_OFF_THRESHOLD,
    MIN_BRIGHTNESS_BEFORE_OFF,
    MAX_BRIGHTNESS,
)

logger = logging.getLogger(__name__)


class StateManager:
    """Manage attention state over time with hysteresis"""

    def __init__(self):
        """Initialize state manager"""
        self.current_state = AttentionState.UNKNOWN
        self.state_start_time = time.time()
        self.state_duration = 0.0

        # Buffer for median filtering
        self.state_buffer = deque(maxlen=STATE_BUFFER_SIZE)

        # Candidate state for confirmation
        self.candidate_state: Optional[AttentionState] = None
        self.candidate_start_time: Optional[float] = None

        logger.info("StateManager initialized")

    def _get_confirmation_delay(self, state: AttentionState) -> float:
        """
        Get required confirmation delay for state

        Args:
            state: The state to confirm

        Returns:
            Delay in seconds
        """
        if state == AttentionState.FOCUSED:
            return FOCUSED_RETURN_DELAY
        elif state == AttentionState.AWAY:
            return AWAY_CONFIRMATION_DELAY
        else:
            return FOCUSED_RETURN_DELAY

    def _get_median_state(self) -> AttentionState:
        """
        Get median state from buffer

        Returns:
            Most common state in buffer
        """
        if not self.state_buffer:
            return AttentionState.UNKNOWN

        # Count occurrences of each state
        state_counts = {}
        for state in self.state_buffer:
            state_counts[state] = state_counts.get(state, 0) + 1

        # Return most common state
        return max(state_counts, key=state_counts.get)

    def update(self, detected_state: AttentionState, confidence: float):
        """
        Update state with new detection

        Args:
            detected_state: Newly detected attention state
            confidence: Confidence score 0.0-1.0
        """
        # Add to buffer
        self.state_buffer.append(detected_state)

        # Get filtered state
        filtered_state = self._get_median_state()

        # Check if we need to transition states
        if filtered_state != self.current_state:
            # New candidate state
            if self.candidate_state != filtered_state:
                self.candidate_state = filtered_state
                self.candidate_start_time = time.time()
                logger.debug(f"New candidate state: {filtered_state.value}")

            # Check if candidate has been confirmed long enough
            if self.candidate_start_time:
                confirmation_time = time.time() - self.candidate_start_time
                required_delay = self._get_confirmation_delay(filtered_state)

                if confirmation_time >= required_delay:
                    # Transition to new state
                    old_state = self.current_state
                    self.current_state = filtered_state
                    self.state_start_time = time.time()
                    self.state_duration = 0.0
                    self.candidate_state = None
                    self.candidate_start_time = None

                    logger.info(f"State transition: {old_state.value} → {self.current_state.value}")
        else:
            # Confirmed current state, reset candidate
            self.candidate_state = None
            self.candidate_start_time = None

        # Update duration in current state
        self.state_duration = time.time() - self.state_start_time

    def get_display_action(self) -> Tuple[float, bool]:
        """
        Get display brightness and power action based on current state

        Returns:
            (target_brightness, should_turn_off_display)
        """
        if self.current_state == AttentionState.FOCUSED:
            # User is focused, full brightness
            return MAX_BRIGHTNESS, False

        elif self.current_state == AttentionState.AWAY:
            # User is away, apply time-based dimming
            if self.state_duration < DIM_THRESHOLD_1:
                # Just turned away, keep full brightness
                return MAX_BRIGHTNESS, False

            elif self.state_duration < DIM_THRESHOLD_2:
                # First dim level
                return DIM_LEVEL_1, False

            elif self.state_duration < DISPLAY_OFF_THRESHOLD:
                # Second dim level
                return DIM_LEVEL_2, False

            else:
                # Turn off display
                return MIN_BRIGHTNESS_BEFORE_OFF, True

        elif self.current_state == AttentionState.DISTRACTED:
            # User is present but not looking, don't change brightness
            # This is a "neutral" state - maintain current level
            return MAX_BRIGHTNESS, False

        else:  # UNKNOWN
            # Cannot determine state, don't change brightness
            return MAX_BRIGHTNESS, False

    def get_state_info(self) -> dict:
        """
        Get current state information for display

        Returns:
            Dictionary with state information
        """
        return {
            'state': self.current_state,
            'duration': self.state_duration,
            'candidate_state': self.candidate_state,
            'candidate_time': (
                time.time() - self.candidate_start_time
                if self.candidate_start_time
                else 0.0
            ),
        }

    def reset(self):
        """Reset state manager"""
        self.current_state = AttentionState.UNKNOWN
        self.state_start_time = time.time()
        self.state_duration = 0.0
        self.state_buffer.clear()
        self.candidate_state = None
        self.candidate_start_time = None
        logger.info("State manager reset")
