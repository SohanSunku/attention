"""
Video capture module with threaded frame grabbing
"""
import cv2
import threading
import time
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class VideoCapture:
    """Thread-safe video capture from webcam"""

    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480):
        """
        Initialize video capture

        Args:
            device_id: Camera device ID (0 for built-in webcam)
            width: Frame width
            height: Frame height
        """
        self.device_id = device_id
        self.width = width
        self.height = height

        self.cap: Optional[cv2.VideoCapture] = None
        self.frame: Optional[np.ndarray] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        self.retry_count = 0
        self.max_retries = 5
        self.retry_delay = 1.0  # seconds

    def _open_camera(self) -> bool:
        """
        Open camera with error handling

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.device_id}")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            # Verify settings
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            logger.info(f"Camera opened: {actual_width}x{actual_height}")

            return True

        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False

    def _capture_loop(self):
        """Background thread for continuous frame capture"""
        logger.info("Starting capture loop")

        while self.running:
            if self.cap is None or not self.cap.isOpened():
                # Try to reopen camera
                if self.retry_count < self.max_retries:
                    logger.warning(f"Camera disconnected, retrying ({self.retry_count + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    if self._open_camera():
                        self.retry_count = 0
                    else:
                        self.retry_count += 1
                else:
                    logger.error("Max retries reached, stopping capture")
                    self.running = False
                    break
                continue

            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
                self.retry_count = 0  # Reset retry count on success
            else:
                logger.warning("Failed to read frame")
                time.sleep(0.1)

        logger.info("Capture loop stopped")

    def start(self) -> bool:
        """
        Start the video capture thread

        Returns:
            True if started successfully
        """
        if self.running:
            logger.warning("Capture already running")
            return True

        if not self._open_camera():
            return False

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        # Wait for first frame
        max_wait = 3.0  # seconds
        start_time = time.time()
        while self.frame is None and time.time() - start_time < max_wait:
            time.sleep(0.1)

        if self.frame is None:
            logger.error("No frame received after start")
            self.stop()
            return False

        logger.info("Video capture started successfully")
        return True

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest frame

        Returns:
            Latest frame as numpy array, or None if not available
        """
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None

    def stop(self):
        """Stop the video capture thread"""
        if not self.running:
            return

        logger.info("Stopping video capture")
        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2.0)

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.frame = None
        logger.info("Video capture stopped")

    def is_available(self) -> bool:
        """
        Check if camera is available and capturing

        Returns:
            True if capturing frames
        """
        return self.running and self.frame is not None

    def __del__(self):
        """Cleanup on deletion"""
        self.stop()
