#!/usr/bin/env python3
"""
Calibration script for attention detection thresholds
Shows live detection values to help tune config.py settings
"""

import cv2
import sys
import time
import numpy as np

# Add project to path
sys.path.insert(0, '/Users/sohan/dev/attention')

from attention_monitor.camera import VideoCapture
from attention_monitor.detector import (
    FaceDetector,
    HeadPoseEstimator,
    GazeEstimator,
    AttentionAnalyzer,
)
from attention_monitor import config

# Colors
GREEN = (0, 255, 0)
YELLOW = (0, 255, 255)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLUE = (255, 165, 0)


def draw_threshold_bar(frame, x, y, value, threshold, label, max_val=1.0, invert=False):
    """
    Draw a horizontal bar showing value vs threshold

    Args:
        frame: Image to draw on
        x, y: Position
        value: Current value
        threshold: Threshold value
        label: Text label
        max_val: Maximum value for scaling
        invert: If True, exceeding threshold turns RED, else GREEN
    """
    bar_width = 300
    bar_height = 20

    # Draw label
    cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

    # Draw background bar
    cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (50, 50, 50), -1)

    # Draw threshold line
    threshold_x = int(x + (threshold / max_val) * bar_width)
    cv2.line(frame, (threshold_x, y), (threshold_x, y + bar_height), YELLOW, 2)

    # Draw value bar
    value_width = int((value / max_val) * bar_width)
    value_width = max(0, min(value_width, bar_width))

    # Color based on threshold
    if invert:
        color = RED if value > threshold else GREEN
    else:
        color = RED if value < threshold else GREEN

    cv2.rectangle(frame, (x, y), (x + value_width, y + bar_height), color, -1)

    # Draw value text
    value_text = f"{value:.2f}"
    cv2.putText(frame, value_text, (x + bar_width + 10, y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)


def draw_angle_indicator(frame, x, y, angle, threshold, label):
    """Draw an angle indicator with threshold markers"""
    radius = 60
    center = (x + radius, y + radius)

    # Draw label
    cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

    # Draw circle
    cv2.circle(frame, center, radius, (50, 50, 50), 2)

    # Draw threshold zones
    # Rotate by -90° so 0° is at top (12 o'clock) instead of right (3 o'clock)
    threshold_rad = np.radians(threshold)
    cv2.ellipse(frame, center, (radius, radius), -90, -threshold, threshold, GREEN, 2)

    # Draw current angle
    angle_rad = np.radians(angle)
    end_x = int(center[0] + radius * np.sin(angle_rad))
    end_y = int(center[1] - radius * np.cos(angle_rad))

    color = RED if abs(angle) > threshold else GREEN
    cv2.line(frame, center, (end_x, end_y), color, 3)

    # Draw angle text
    angle_text = f"{angle:.1f}°"
    cv2.putText(frame, angle_text, (center[0] - 25, center[1] + radius + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Draw threshold text
    threshold_text = f"±{threshold}°"
    cv2.putText(frame, threshold_text, (center[0] - 20, center[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, YELLOW, 1)


def main():
    """Run calibration interface"""
    print("=" * 60)
    print("ATTENTION MONITOR - CALIBRATION MODE")
    print("=" * 60)
    print("\nThis tool helps you tune detection thresholds.")
    print("\nInstructions:")
    print("  - Look at different positions (left, right, up, down)")
    print("  - Watch the bars and angles to see current values")
    print("  - Note values when detection is wrong")
    print("  - Adjust thresholds in config.py accordingly")
    print("\nControls:")
    print("  - Press 'q' to quit")
    print("  - Press 's' to save current values to a log")
    print("\nCurrent thresholds from config.py:")
    print(f"  HEAD_POSE_YAW_THRESHOLD = {config.HEAD_POSE_YAW_THRESHOLD}°")
    print(f"  HEAD_POSE_PITCH_THRESHOLD = {config.HEAD_POSE_PITCH_THRESHOLD}°")
    print(f"  EYE_ASPECT_RATIO_THRESHOLD = {config.EYE_ASPECT_RATIO_THRESHOLD}")
    print(f"  GAZE_AWAY_THRESHOLD = {config.GAZE_AWAY_THRESHOLD}")
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    # Initialize components
    camera = VideoCapture(config.CAMERA_DEVICE_ID, config.CAMERA_WIDTH, config.CAMERA_HEIGHT)
    face_detector = FaceDetector()
    head_pose_estimator = HeadPoseEstimator()
    gaze_estimator = GazeEstimator()
    attention_analyzer = AttentionAnalyzer()

    if not camera.start():
        print("ERROR: Failed to start camera")
        return 1

    print("Camera started. Opening calibration window...\n")

    # Create log for saving snapshots
    log_entries = []

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            # Create display frame (larger to fit all info)
            display = np.zeros((800, 1200, 3), dtype=np.uint8)

            # Place camera feed in top left
            h, w = frame.shape[:2]
            display[0:h, 0:w] = frame

            # Detect face
            landmarks = face_detector.detect(frame)

            # Define info panel position (used in both branches)
            info_x = w + 20
            info_y = 30

            if landmarks is not None:
                # Draw landmarks on camera feed
                for i in range(min(468, len(landmarks))):
                    x, y = int(landmarks[i][0]), int(landmarks[i][1])
                    cv2.circle(display, (x, y), 1, GREEN, -1)

                # Draw iris
                for i in range(468, min(478, len(landmarks))):
                    x, y = int(landmarks[i][0]), int(landmarks[i][1])
                    cv2.circle(display, (x, y), 2, BLUE, -1)

                # Get detection values
                head_pose_angles = head_pose_estimator.estimate(landmarks, frame.shape[:2])
                gaze_info = gaze_estimator.estimate(landmarks)
                attention_state, confidence = attention_analyzer.analyze(
                    landmarks, head_pose_angles, gaze_info
                )

                # Title
                cv2.putText(display, "CALIBRATION MODE", (info_x, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)
                info_y += 40

                # Attention State
                state_color = attention_analyzer.get_state_color(attention_state)
                cv2.putText(display, f"State: {attention_state.value.upper()}",
                           (info_x, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)
                cv2.putText(display, f"Confidence: {confidence:.2f}",
                           (info_x + 250, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
                info_y += 50

                # Head Pose Section
                if head_pose_angles:
                    yaw, pitch, roll = head_pose_angles

                    cv2.putText(display, "HEAD POSE", (info_x, info_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
                    info_y += 30

                    # Yaw angle indicator
                    draw_angle_indicator(display, info_x, info_y, yaw,
                                        config.HEAD_POSE_YAW_THRESHOLD, "YAW (left/right)")

                    # Pitch angle indicator
                    draw_angle_indicator(display, info_x + 180, info_y, pitch,
                                        config.HEAD_POSE_PITCH_THRESHOLD, "PITCH (up/down)")

                    info_y += 150

                # Gaze Section
                if gaze_info:
                    cv2.putText(display, "GAZE TRACKING", (info_x, info_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
                    info_y += 30

                    # Left gaze bar
                    draw_threshold_bar(display, info_x, info_y,
                                      gaze_info['left_gaze'],
                                      config.GAZE_AWAY_THRESHOLD,
                                      "Left Gaze (0=left, 1=right)",
                                      max_val=1.0, invert=False)
                    info_y += 40

                    # Right gaze bar
                    draw_threshold_bar(display, info_x, info_y,
                                      gaze_info['right_gaze'],
                                      config.GAZE_AWAY_THRESHOLD,
                                      "Right Gaze",
                                      max_val=1.0, invert=False)
                    info_y += 40

                    # Draw center zone reference
                    center_text = f"Center zone: {config.GAZE_CENTER_MIN}-{config.GAZE_CENTER_MAX}"
                    cv2.putText(display, center_text, (info_x, info_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, YELLOW, 1)
                    info_y += 30

                    # Left EAR bar
                    draw_threshold_bar(display, info_x, info_y,
                                      gaze_info['left_ear'],
                                      config.EYE_ASPECT_RATIO_THRESHOLD,
                                      "Left Eye Aspect Ratio",
                                      max_val=0.4, invert=False)
                    info_y += 40

                    # Right EAR bar
                    draw_threshold_bar(display, info_x, info_y,
                                      gaze_info['right_ear'],
                                      config.EYE_ASPECT_RATIO_THRESHOLD,
                                      "Right Eye Aspect Ratio",
                                      max_val=0.4, invert=False)
                    info_y += 40

                    # Eyes closed indicator
                    eyes_status = "CLOSED" if gaze_info['eyes_closed'] else "OPEN"
                    eyes_color = RED if gaze_info['eyes_closed'] else GREEN
                    cv2.putText(display, f"Eyes: {eyes_status}", (info_x, info_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, eyes_color, 2)
                    info_y += 50

                # Instructions
                info_y = 650
                cv2.putText(display, "INSTRUCTIONS", (info_x, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)
                info_y += 25

                instructions = [
                    "Look: Center, Left, Right, Up, Down",
                    "Close your eyes briefly",
                    "Watch bars - GREEN=OK, RED=threshold exceeded",
                    "Yellow line = threshold value",
                    "",
                    "Press 'q' to quit",
                    "Press 's' to save current values to log"
                ]

                for instruction in instructions:
                    cv2.putText(display, instruction, (info_x, info_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, WHITE, 1)
                    info_y += 20

            else:
                # No face detected
                cv2.putText(display, "NO FACE DETECTED", (info_x, 100),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, RED, 2)
                cv2.putText(display, "Position your face in the camera view",
                           (info_x, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)

            # Show frame
            cv2.imshow('Attention Monitor - Calibration', display)

            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nQuitting calibration...")
                break
            elif key == ord('s') and landmarks is not None:
                # Save snapshot
                timestamp = time.strftime("%H:%M:%S")
                entry = {
                    'time': timestamp,
                    'state': attention_state.value if landmarks is not None else 'none',
                    'yaw': yaw if head_pose_angles else 0,
                    'pitch': pitch if head_pose_angles else 0,
                    'left_gaze': gaze_info['left_gaze'] if gaze_info else 0,
                    'right_gaze': gaze_info['right_gaze'] if gaze_info else 0,
                    'left_ear': gaze_info['left_ear'] if gaze_info else 0,
                    'right_ear': gaze_info['right_ear'] if gaze_info else 0,
                }
                log_entries.append(entry)
                print(f"\n[{timestamp}] Saved snapshot: state={entry['state']}, "
                      f"yaw={entry['yaw']:.1f}°, pitch={entry['pitch']:.1f}°")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    finally:
        camera.stop()
        cv2.destroyAllWindows()

        # Print log summary
        if log_entries:
            print("\n" + "=" * 60)
            print("SAVED SNAPSHOTS")
            print("=" * 60)
            print(f"{'Time':<10} {'State':<12} {'Yaw':<8} {'Pitch':<8} {'L.Gaze':<8} {'R.Gaze':<8}")
            print("-" * 60)
            for entry in log_entries:
                print(f"{entry['time']:<10} {entry['state']:<12} "
                      f"{entry['yaw']:>6.1f}°  {entry['pitch']:>6.1f}°  "
                      f"{entry['left_gaze']:>6.2f}  {entry['right_gaze']:>6.2f}")

            # Save to file
            log_file = "/Users/sohan/dev/attention/calibration_log.txt"
            with open(log_file, 'w') as f:
                f.write("ATTENTION MONITOR - CALIBRATION LOG\n")
                f.write("=" * 60 + "\n\n")
                f.write("Current thresholds:\n")
                f.write(f"  HEAD_POSE_YAW_THRESHOLD = {config.HEAD_POSE_YAW_THRESHOLD}\n")
                f.write(f"  HEAD_POSE_PITCH_THRESHOLD = {config.HEAD_POSE_PITCH_THRESHOLD}\n")
                f.write(f"  EYE_ASPECT_RATIO_THRESHOLD = {config.EYE_ASPECT_RATIO_THRESHOLD}\n")
                f.write(f"  GAZE_AWAY_THRESHOLD = {config.GAZE_AWAY_THRESHOLD}\n\n")
                f.write("Snapshots:\n")
                f.write("-" * 60 + "\n")
                for entry in log_entries:
                    f.write(f"[{entry['time']}] State: {entry['state']}, "
                           f"Yaw: {entry['yaw']:.1f}°, Pitch: {entry['pitch']:.1f}°, "
                           f"L.Gaze: {entry['left_gaze']:.2f}, R.Gaze: {entry['right_gaze']:.2f}, "
                           f"L.EAR: {entry['left_ear']:.2f}, R.EAR: {entry['right_ear']:.2f}\n")

            print(f"\nLog saved to: {log_file}")

        print("\nCalibration complete!")

    return 0


if __name__ == '__main__':
    sys.exit(main())
