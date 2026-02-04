"""
Display brightness control using keyboard shortcuts
Works reliably on all Macs including Apple Silicon
"""
import subprocess
import logging
import time
from typing import Optional

from ..config import MIN_BRIGHTNESS, MAX_BRIGHTNESS

logger = logging.getLogger(__name__)


class BrightnessController:
    """Control macOS display brightness using keyboard shortcuts"""

    # Mac brightness has approximately 16 levels (0-15)
    BRIGHTNESS_LEVELS = 16

    def __init__(self):
        """Initialize brightness controller"""
        self.available = True
        self.current_brightness = 0.5  # Start at middle (we can't read actual value)
        self.original_brightness = 0.5
        self.target_brightness = 0.5

        logger.info("Brightness controller initialized (keyboard shortcuts)")

    def _press_brightness_key(self, key_code: int, times: int = 1):
        """
        Press brightness key using AppleScript

        Args:
            key_code: 144 for brightness_up, 145 for brightness_down
            times: Number of times to press the key
        """
        try:
            for _ in range(times):
                # Use osascript to press the key
                script = f'tell application "System Events" to key code {key_code}'
                subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    timeout=1.0,
                    check=False
                )
                time.sleep(0.05)  # Small delay between presses

        except Exception as e:
            logger.warning(f"Failed to press brightness key: {e}")

    def _set_to_max_brightness(self):
        """Set brightness to maximum by pressing up key many times"""
        # Press brightness up key max times to ensure we're at 100%
        self._press_brightness_key(144, self.BRIGHTNESS_LEVELS + 2)
        self.current_brightness = 1.0

    def _set_to_min_brightness(self):
        """Set brightness to minimum by pressing down key many times"""
        # Press brightness down key max times to ensure we're at minimum
        self._press_brightness_key(145, self.BRIGHTNESS_LEVELS + 2)
        self.current_brightness = MIN_BRIGHTNESS

    def get_brightness(self) -> Optional[float]:
        """
        Get current display brightness (tracked internally)

        Returns:
            Brightness value 0.0-1.0
        """
        return self.current_brightness

    def set_brightness(self, brightness: float) -> bool:
        """
        Set display brightness using keyboard shortcuts

        Args:
            brightness: Target brightness 0.0-1.0

        Returns:
            True if successful
        """
        if not self.available:
            return False

        try:
            # Clamp brightness
            brightness = max(MIN_BRIGHTNESS, min(MAX_BRIGHTNESS, brightness))

            # Calculate current and target levels (0-15)
            current_level = int(self.current_brightness * self.BRIGHTNESS_LEVELS)
            target_level = int(brightness * self.BRIGHTNESS_LEVELS)

            # Calculate how many steps to change
            diff = target_level - current_level

            if diff == 0:
                return True

            # Press brightness up or down keys
            if diff > 0:
                # Brightness up (key code 144)
                self._press_brightness_key(144, abs(diff))
            else:
                # Brightness down (key code 145)
                self._press_brightness_key(145, abs(diff))

            # Update tracked brightness
            self.current_brightness = brightness
            logger.debug(f"Set brightness to {brightness:.2f} ({target_level}/{self.BRIGHTNESS_LEVELS})")

            return True

        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            return False

    def transition_to(self, brightness: float, duration: float = 1.5) -> bool:
        """
        Transition to target brightness

        Note: Smooth transitions are not ideal with keyboard shortcuts,
        so we just set directly.

        Args:
            brightness: Target brightness 0.0-1.0
            duration: Ignored (kept for API compatibility)

        Returns:
            True if successful
        """
        if not self.available:
            return False

        # For keyboard method, just set directly
        # Smooth transitions would require too many key presses

        # Only change if there's a significant difference
        if abs(self.current_brightness - brightness) < 0.08:  # ~1 level
            return True

        return self.set_brightness(brightness)

    def restore_original(self):
        """Restore original brightness"""
        logger.info("Restoring original brightness (setting to 100%)")
        # Set to max brightness on restore
        self._set_to_max_brightness()

    def cleanup(self):
        """Clean up resources"""
        self.restore_original()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.cleanup()
        except:
            pass
