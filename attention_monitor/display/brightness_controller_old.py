"""
Display brightness control using PyObjC/Quartz
"""
import logging
import time
import threading
from typing import Optional

try:
    from Quartz import CoreGraphics as CG
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    logging.warning("PyObjC not available, brightness control disabled")

from ..config import MIN_BRIGHTNESS, MAX_BRIGHTNESS, TRANSITION_DURATION

logger = logging.getLogger(__name__)


class BrightnessController:
    """Control macOS display brightness"""

    def __init__(self):
        """Initialize brightness controller"""
        self.available = QUARTZ_AVAILABLE
        self.display_id = None
        self.original_brightness = None
        self.current_brightness = None
        self.target_brightness = None
        self.transition_thread: Optional[threading.Thread] = None
        self.transitioning = False

        if self.available:
            self._initialize_display()

    def _initialize_display(self):
        """Get main display and store original brightness"""
        try:
            # Get main display ID
            self.display_id = CG.CGMainDisplayID()

            # Get current brightness
            _, brightness = CG.CGDisplayGetBrightness(self.display_id)
            self.original_brightness = brightness
            self.current_brightness = brightness
            self.target_brightness = brightness

            logger.info(f"Display initialized, current brightness: {brightness:.2f}")

        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            self.available = False

    def get_brightness(self) -> Optional[float]:
        """
        Get current display brightness

        Returns:
            Brightness value 0.0-1.0, or None if not available
        """
        if not self.available:
            return None

        try:
            _, brightness = CG.CGDisplayGetBrightness(self.display_id)
            return brightness
        except Exception as e:
            logger.error(f"Failed to get brightness: {e}")
            return None

    def set_brightness(self, brightness: float) -> bool:
        """
        Set display brightness immediately

        Args:
            brightness: Target brightness 0.0-1.0

        Returns:
            True if successful
        """
        if not self.available:
            return False

        # Clamp to valid range
        brightness = max(MIN_BRIGHTNESS, min(MAX_BRIGHTNESS, brightness))

        try:
            CG.CGDisplaySetBrightness(self.display_id, brightness)
            self.current_brightness = brightness
            return True
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            return False

    def _transition_worker(self, target: float, duration: float):
        """
        Worker thread for smooth brightness transitions

        Args:
            target: Target brightness
            duration: Transition duration in seconds
        """
        start_brightness = self.current_brightness
        start_time = time.time()

        while self.transitioning:
            elapsed = time.time() - start_time

            if elapsed >= duration:
                # Transition complete
                self.set_brightness(target)
                break

            # Ease-out cubic easing
            progress = elapsed / duration
            eased_progress = 1 - pow(1 - progress, 3)

            # Interpolate brightness
            current = start_brightness + (target - start_brightness) * eased_progress
            self.set_brightness(current)

            # Small sleep to avoid busy-waiting
            time.sleep(0.03)  # ~30fps

        self.transitioning = False

    def transition_to(self, brightness: float, duration: float = TRANSITION_DURATION) -> bool:
        """
        Smoothly transition to target brightness

        Args:
            brightness: Target brightness 0.0-1.0
            duration: Transition duration in seconds

        Returns:
            True if transition started successfully
        """
        if not self.available:
            return False

        # Clamp to valid range
        brightness = max(MIN_BRIGHTNESS, min(MAX_BRIGHTNESS, brightness))

        # If already at target, do nothing
        if abs(self.current_brightness - brightness) < 0.01:
            return True

        # Stop any existing transition
        if self.transitioning:
            self.transitioning = False
            if self.transition_thread:
                self.transition_thread.join(timeout=1.0)

        # Start new transition
        self.target_brightness = brightness
        self.transitioning = True
        self.transition_thread = threading.Thread(
            target=self._transition_worker,
            args=(brightness, duration),
            daemon=True
        )
        self.transition_thread.start()

        logger.debug(f"Transitioning brightness: {self.current_brightness:.2f} → {brightness:.2f}")
        return True

    def restore_original(self):
        """Restore original brightness on cleanup"""
        if self.available and self.original_brightness is not None:
            logger.info(f"Restoring original brightness: {self.original_brightness:.2f}")
            self.set_brightness(self.original_brightness)

    def cleanup(self):
        """Clean up resources"""
        # Stop any transition
        if self.transitioning:
            self.transitioning = False
            if self.transition_thread:
                self.transition_thread.join(timeout=1.0)

        # Restore original brightness
        self.restore_original()

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()
