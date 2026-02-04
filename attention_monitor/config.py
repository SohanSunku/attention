"""
Configuration file for Attention Monitor
Single source of truth for all thresholds and settings
"""

# === ATTENTION DETECTION THRESHOLDS ===

# Head Pose - AWAY thresholds (must exceed to trigger AWAY)
HEAD_POSE_YAW_THRESHOLD = 40        # degrees - head turned left/right (less sensitive)
HEAD_POSE_PITCH_THRESHOLD = 20      # degrees - head tilted up/down

# Head Pose - DISTRACTED thresholds (moderate turn, between FOCUSED and AWAY)
HEAD_POSE_YAW_DISTRACTED = 60       # degrees - moderate yaw triggers DISTRACTED
HEAD_POSE_PITCH_DISTRACTED = 18     # degrees - moderate pitch triggers DISTRACTED

# Eye tracking
EYE_ASPECT_RATIO_THRESHOLD = 0.15   # eyes closed if below this (harder to trigger)

# Gaze - definite away (triggers DISTRACTED immediately)
GAZE_CENTER_MIN = 0.35              # left boundary of center gaze
GAZE_CENTER_MAX = 0.55              # right boundary of center gaze (wider center zone)
GAZE_AWAY_THRESHOLD = 0.15          # definite look away (used by gaze_estimator)

# Gaze - slight away (reduces confidence, may trigger DISTRACTED)
GAZE_SLIGHT_AWAY_MIN = 0.20         # slight look away threshold (left)
GAZE_SLIGHT_AWAY_MAX = 0.80         # slight look away threshold (right)

# === AGGRESSIVE TIMING (user preference) ===
AWAY_CONFIRMATION_DELAY = 0.0       # seconds - INSTANT state change (zero delay)
FOCUSED_RETURN_DELAY = 0.0          # seconds - INSTANT return when focused

DIM_THRESHOLD_1 = 0.0               # seconds away → dim IMMEDIATELY to 50%
DIM_LEVEL_1 = 0.5                   # brightness level

DIM_THRESHOLD_2 = 7.0               # seconds away → dim to 20%
DIM_LEVEL_2 = 0.2                   # brightness level

DISPLAY_OFF_THRESHOLD = 20.0        # seconds away → turn off display
MIN_BRIGHTNESS_BEFORE_OFF = 0.05    # minimum brightness before turning off
ENABLE_DISPLAY_SLEEP = False        # enable/disable display sleep feature (pmset)

# === DISPLAY CONTROL ===
MIN_BRIGHTNESS = 0.05               # never go completely dark (safety)
MAX_BRIGHTNESS = 1.0                # full brightness
TRANSITION_DURATION = 0.1           # seconds for INSTANT brightness changes

# === CAMERA SETTINGS ===
CAMERA_DEVICE_ID = 0                # built-in webcam
CAMERA_WIDTH = 640                  # frame width (balance performance/accuracy)
CAMERA_HEIGHT = 480                 # frame height
TARGET_FPS = 30                     # target frame rate

# === STATE MANAGEMENT ===
STATE_BUFFER_SIZE = 1               # frames for median filtering (1 = instant, no smoothing)
MEDIAN_FILTER_WINDOW = 10           # smooth state transitions

# === MEDIAPIPE SETTINGS ===
MEDIAPIPE_MAX_FACES = 1             # only track one face
MEDIAPIPE_REFINE_LANDMARKS = True   # enable iris tracking
MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.5
MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5
