"""
Configuration file for Attention Monitor
Single source of truth for all thresholds and settings
"""

# === ATTENTION DETECTION THRESHOLDS ===

# Head Pose - AWAY thresholds (must exceed to trigger AWAY)
HEAD_POSE_YAW_THRESHOLD = 40        # degrees - head turned left/right (less sensitive)
HEAD_POSE_PITCH_THRESHOLD = 15      # degrees - head tilted up/down

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

# General state change hold time - applies to ALL state transitions
STATE_HOLD_TIME = 1.0               # seconds - how long a new state must hold before registering

# Legacy specific delays (STATE_HOLD_TIME overrides these if higher)
AWAY_CONFIRMATION_DELAY = 0.2       # seconds - minimal delay to prevent flicker
FOCUSED_RETURN_DELAY = 0.0          # seconds - return delay

DIM_THRESHOLD_1 = 0.0               # seconds away → dim IMMEDIATELY to 5%
DIM_LEVEL_1 = 0.05                  # brightness level (5% when AWAY)

DIM_THRESHOLD_2 = 999.0             # disabled - no intermediate step
DIM_LEVEL_2 = 0.0                   # disabled

DISPLAY_OFF_THRESHOLD = 999.0       # disabled - using brightness 0% instead
MIN_BRIGHTNESS_BEFORE_OFF = 0.0     # not used
ENABLE_DISPLAY_SLEEP = False        # enable/disable display sleep feature (pmset)

# === DISPLAY CONTROL ===

# Brightness levels for different states
BRIGHTNESS_FOCUSED = 0.5            # brightness when FOCUSED (50%)
BRIGHTNESS_AWAY = 0.05              # brightness when AWAY (5%)
BRIGHTNESS_DISTRACTED = 0.5         # brightness when DISTRACTED (50%, same as focused)

# Legacy compatibility (can be removed if not used elsewhere)
MIN_BRIGHTNESS = 0.0                # minimum allowed brightness (for safety)
MAX_BRIGHTNESS = 0.5                # maximum allowed brightness

TRANSITION_DURATION = 0.1           # seconds for brightness changes

# === CAMERA SETTINGS ===
CAMERA_DEVICE_ID = 0                # built-in webcam
CAMERA_WIDTH = 640                  # frame width (balance performance/accuracy)
CAMERA_HEIGHT = 480                 # frame height
TARGET_FPS = 30                     # target frame rate

# === STATE MANAGEMENT ===
STATE_BUFFER_SIZE = 5               # frames for median filtering (minimal smoothing to prevent flicker)
MEDIAN_FILTER_WINDOW = 10           # smooth state transitions

# === MEDIAPIPE SETTINGS ===
MEDIAPIPE_MAX_FACES = 1             # only track one face
MEDIAPIPE_REFINE_LANDMARKS = True   # enable iris tracking
MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.5
MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5
