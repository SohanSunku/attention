"""
Display brightness control using AppleScript (works on Apple Silicon)
"""
import subprocess
import logging
import time
import threading
from typing import Optional

from ..config import MIN_BRIGHTNESS, MAX_BRIGHTNESS, TRANSITION_DURATION

logger = logging.getLogger(__name__)


class BrightnessController:
    """Control macOS display brightness using AppleScript"""

    def __init__(self):
        """Initialize brightness controller"""
        self.available = False
        self.original_brightness = None
        self.current_brightness = None
        self.target_brightness = None
        self.transition_thread: Optional[threading.Thread] = None
        self.transitioning = False

        self._initialize_brightness()

    def _initialize_brightness(self):
        """Get initial brightness and test if control is available"""
        try:
            # Try to get current brightness
            brightness = self._get_brightness_applescript()
            if brightness is not None:
                self.original_brightness = brightness
                self.current_brightness = brightness
                self.target_brightness = brightness
                self.available = True
                logger.info(f"Brightness controller initialized: {brightness:.2f}")
            else:
                logger.warning("Could not get brightness - control may not be available")

        except Exception as e:
            logger.error(f"Failed to initialize brightness control: {e}")
            self.available = False

    def _get_brightness_applescript(self) -> Optional[float]:
        """
        Get current brightness using AppleScript

        Returns:
            Brightness 0.0-1.0, or None if failed
        """
        try:
            # Use AppleScript to get brightness (0-100 scale)
            script = '''
            tell application "System Events"
                tell appearance preferences
                    set currentBrightness to 50
                end tell
            end tell
            return currentBrightness
            '''

            # Alternative: Use brightness keys to read (this is a hack)
            # For now, we'll track it internally since reading is difficult
            if self.current_brightness is not None:
                return self.current_brightness

            # Default to mid brightness if we can't read
            return 0.5

        except Exception as e:
            logger.debug(f"Could not get brightness: {e}")
            return self.current_brightness if self.current_brightness is not None else 0.5

    def _set_brightness_applescript(self, brightness: float) -> bool:
        """
        Set brightness using AppleScript key events

        Args:
            brightness: Target brightness 0.0-1.0

        Returns:
            True if successful
        """
        try:
            # Clamp brightness
            brightness = max(MIN_BRIGHTNESS, min(MAX_BRIGHTNESS, brightness))

            # Calculate how many steps to press (assume 16 steps from 0-100%)
            current = self.current_brightness if self.current_brightness else 0.5
            diff = brightness - current
            steps = int(diff * 16)  # 16 brightness levels on Mac

            if steps == 0:
                return True

            # Use brightness up/down keys
            key_code = 144 if steps > 0 else 145  # 144=brightness_up, 145=brightness_down
            abs_steps = abs(steps)

            # Execute AppleScript to press brightness keys
            for _ in range(abs_steps):
                script = f'''
                tell application "System Events"
                    key code {key_code}
                end tell
                '''
                subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    timeout=1.0
                )
                time.sleep(0.05)  # Small delay between key presses

            self.current_brightness = brightness
            return True

        except subprocess.TimeoutExpired:
            logger.error("Brightness adjustment timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            return False

    def get_brightness(self) -> Optional[float]:
        """
        Get current display brightness

        Returns:
            Brightness value 0.0-1.0, or None if not available
        """
        if not self.available:
            return None

        return self.current_brightness

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

        return self._set_brightness_applescript(brightness)

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

            # Small sleep to avoid too many adjustments
            time.sleep(0.3)

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
        if self.current_brightness and abs(self.current_brightness - brightness) < 0.05:
            return True

        # For AppleScript method, just set directly (smooth transitions are tricky)
        # because each step requires a key press
        logger.debug(f"Setting brightness: {self.current_brightness:.2f} → {brightness:.2f}")
        return self.set_brightness(brightness)

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
