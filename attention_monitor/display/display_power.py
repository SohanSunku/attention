"""
Display power control using macOS pmset and caffeinate
"""
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DisplayPowerController:
    """Control display power (sleep/wake)"""

    def __init__(self):
        """Initialize display power controller"""
        self.caffeinate_process: Optional[subprocess.Popen] = None
        self.sleep_prevented = False
        logger.info("DisplayPowerController initialized")

    def turn_off_display(self) -> bool:
        """
        Turn off display using pmset

        Returns:
            True if successful
        """
        try:
            # Stop preventing sleep first
            if self.sleep_prevented:
                self.prevent_sleep(False)

            # Run pmset to sleep display
            result = subprocess.run(
                ['pmset', 'displaysleepnow'],
                capture_output=True,
                text=True,
                timeout=5.0
            )

            if result.returncode == 0:
                logger.info("Display turned off")
                return True
            else:
                logger.warning(f"pmset failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("pmset command timed out")
            return False
        except FileNotFoundError:
            logger.error("pmset command not found")
            return False
        except Exception as e:
            logger.error(f"Failed to turn off display: {e}")
            return False

    def prevent_sleep(self, enable: bool = True) -> bool:
        """
        Prevent display from sleeping using caffeinate

        Args:
            enable: True to prevent sleep, False to allow sleep

        Returns:
            True if successful
        """
        if enable:
            if self.sleep_prevented:
                return True  # Already preventing sleep

            try:
                # Start caffeinate process to prevent display sleep
                # -d flag prevents display from sleeping
                self.caffeinate_process = subprocess.Popen(
                    ['caffeinate', '-d'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.sleep_prevented = True
                logger.debug("Started preventing display sleep")
                return True

            except FileNotFoundError:
                logger.error("caffeinate command not found")
                return False
            except Exception as e:
                logger.error(f"Failed to start caffeinate: {e}")
                return False

        else:
            if not self.sleep_prevented:
                return True  # Already allowing sleep

            try:
                # Stop caffeinate process
                if self.caffeinate_process:
                    self.caffeinate_process.terminate()
                    try:
                        self.caffeinate_process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        self.caffeinate_process.kill()
                        self.caffeinate_process.wait()

                    self.caffeinate_process = None

                self.sleep_prevented = False
                logger.debug("Stopped preventing display sleep")
                return True

            except Exception as e:
                logger.error(f"Failed to stop caffeinate: {e}")
                return False

    def cleanup(self):
        """Clean up resources"""
        # Stop preventing sleep
        if self.sleep_prevented:
            self.prevent_sleep(False)

        logger.info("DisplayPowerController cleaned up")

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()
