"""
Main entry point for Attention Monitor
"""
import argparse
import logging
import sys
import time
import signal
import cv2
from typing import Optional

from .camera import VideoCapture
from .detector import (
    FaceDetector,
    HeadPoseEstimator,
    GazeEstimator,
    AttentionAnalyzer,
    AttentionState,
)
from .display import BrightnessController, DisplayPowerController
from .state import StateManager
from .config import (
    CAMERA_DEVICE_ID,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    TARGET_FPS,
)

# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """Handle Ctrl+C for graceful shutdown"""
    global running
    print("\nShutting down...")
    running = False


def setup_logging(log_level: str):
    """
    Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def draw_debug_overlay(
    frame,
    landmarks,
    head_pose_angles,
    gaze_info,
    state: AttentionState,
    confidence: float,
    state_info: dict,
    target_brightness: float,
):
    """
    Draw debug information on frame

    Args:
        frame: BGR image
        landmarks: Face landmarks
        head_pose_angles: (yaw, pitch, roll) tuple
        gaze_info: Gaze estimation dict
        state: Current attention state
        confidence: State confidence
        state_info: State manager info
        target_brightness: Target brightness level
    """
    overlay = frame.copy()

    # Draw landmarks
    if landmarks is not None:
        # Face mesh points
        for i in range(min(468, len(landmarks))):
            x, y = int(landmarks[i][0]), int(landmarks[i][1])
            cv2.circle(overlay, (x, y), 1, (0, 255, 0), -1)

        # Iris landmarks
        iris_indices = list(range(468, 478))
        for i in iris_indices:
            if i < len(landmarks):
                x, y = int(landmarks[i][0]), int(landmarks[i][1])
                cv2.circle(overlay, (x, y), 2, (255, 0, 0), -1)

    # Draw text overlay
    y_offset = 30
    line_height = 30

    # State
    state_color = (0, 255, 0) if state == AttentionState.FOCUSED else (0, 255, 255) if state == AttentionState.DISTRACTED else (0, 0, 255)
    cv2.putText(
        overlay,
        f"State: {state.value.upper()} (conf: {confidence:.2f})",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        state_color,
        2
    )

    # Duration
    y_offset += line_height
    cv2.putText(
        overlay,
        f"Duration: {state_info['duration']:.1f}s",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # Head pose
    if head_pose_angles:
        y_offset += line_height
        yaw, pitch, roll = head_pose_angles
        cv2.putText(
            overlay,
            f"Head: Yaw={yaw:.1f} Pitch={pitch:.1f}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

    # Gaze
    if gaze_info:
        y_offset += line_height
        cv2.putText(
            overlay,
            f"Gaze L: {gaze_info['left_gaze']:.2f}  R: {gaze_info['right_gaze']:.2f}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        y_offset += line_height
        cv2.putText(
            overlay,
            f"EAR L: {gaze_info['left_ear']:.2f}  R: {gaze_info['right_ear']:.2f}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

    # Brightness
    y_offset += line_height
    cv2.putText(
        overlay,
        f"Brightness: {int(target_brightness * 100)}%",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # Instructions
    y_offset = overlay.shape[0] - 20
    cv2.putText(
        overlay,
        "Press 'q' to quit, 'p' to pause, 'r' to reset",
        (10, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1
    )

    return overlay


def main():
    """Main application loop"""
    global running

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Attention Monitor - Control display brightness based on user attention'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show camera feed with face landmarks'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Monitor only, no brightness changes'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting Attention Monitor")
    logger.info(f"Debug mode: {args.debug}, Dry run: {args.dry_run}")

    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize components
    try:
        logger.info("Initializing components...")

        camera = VideoCapture(CAMERA_DEVICE_ID, CAMERA_WIDTH, CAMERA_HEIGHT)
        face_detector = FaceDetector()
        head_pose_estimator = HeadPoseEstimator()
        gaze_estimator = GazeEstimator()
        attention_analyzer = AttentionAnalyzer()
        brightness_controller = BrightnessController()
        display_power = DisplayPowerController()
        state_manager = StateManager()

        logger.info("Components initialized")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return 1

    # Start camera
    if not camera.start():
        logger.error("Failed to start camera")
        return 1

    logger.info("Camera started successfully")

    # Main loop
    paused = False
    frame_count = 0
    start_time = time.time()

    try:
        while running:
            loop_start = time.time()

            # Get frame
            frame = camera.get_frame()
            if frame is None:
                logger.warning("No frame available")
                time.sleep(0.1)
                continue

            if not paused:
                # Detect face landmarks
                landmarks = face_detector.detect(frame)

                # Estimate head pose
                head_pose_angles = None
                if landmarks is not None:
                    head_pose_angles = head_pose_estimator.estimate(landmarks, frame.shape[:2])

                # Estimate gaze
                gaze_info = None
                if landmarks is not None:
                    gaze_info = gaze_estimator.estimate(landmarks)

                # Analyze attention state
                attention_state, confidence = attention_analyzer.analyze(
                    landmarks, head_pose_angles, gaze_info
                )

                # Update state manager
                state_manager.update(attention_state, confidence)

                # Get display action
                target_brightness, should_turn_off = state_manager.get_display_action()

                # Apply display changes (unless dry run)
                if not args.dry_run:
                    if should_turn_off:
                        display_power.turn_off_display()
                    else:
                        brightness_controller.transition_to(target_brightness)
                        display_power.prevent_sleep(True)

                # Log state transitions
                if frame_count % 30 == 0:  # Every ~1 second
                    state_info = state_manager.get_state_info()
                    logger.debug(
                        f"State: {attention_state.value}, "
                        f"Duration: {state_info['duration']:.1f}s, "
                        f"Brightness: {int(target_brightness * 100)}%"
                    )

            # Debug visualization
            if args.debug:
                state_info = state_manager.get_state_info()
                debug_frame = draw_debug_overlay(
                    frame,
                    landmarks if not paused else None,
                    head_pose_angles if not paused else None,
                    gaze_info if not paused else None,
                    state_manager.current_state,
                    confidence if not paused else 0.0,
                    state_info,
                    target_brightness if not paused else 1.0,
                )

                cv2.imshow('Attention Monitor - Debug', debug_frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("User requested quit")
                    break
                elif key == ord('p'):
                    paused = not paused
                    logger.info(f"{'Paused' if paused else 'Resumed'}")
                elif key == ord('r'):
                    state_manager.reset()
                    logger.info("State manager reset")

            # Frame rate control
            frame_count += 1
            elapsed = time.time() - loop_start
            sleep_time = max(0, (1.0 / TARGET_FPS) - elapsed)
            time.sleep(sleep_time)

    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
        return 1

    finally:
        # Cleanup
        logger.info("Cleaning up...")

        running = False
        camera.stop()
        face_detector.close()

        if not args.dry_run:
            brightness_controller.cleanup()
            display_power.cleanup()

        if args.debug:
            cv2.destroyAllWindows()

        # Print statistics
        elapsed_time = time.time() - start_time
        fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        logger.info(f"Processed {frame_count} frames in {elapsed_time:.1f}s ({fps:.1f} fps)")
        logger.info("Shutdown complete")

    return 0


if __name__ == '__main__':
    sys.exit(main())
