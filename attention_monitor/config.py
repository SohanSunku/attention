"""
Configuration file for Attention Monitor
Single source of truth for all thresholds and settings
"""

# === ATTENTION DETECTION THRESHOLDS ===
HEAD_POSE_YAW_THRESHOLD = 30        # degrees - head turned left/right
HEAD_POSE_PITCH_THRESHOLD = 20      # degrees - head tilted up/down
EYE_ASPECT_RATIO_THRESHOLD = 0.2    # eyes closed if below this
GAZE_CENTER_MIN = 0.35              # left boundary of center gaze
GAZE_CENTER_MAX = 0.65              # right boundary of center gaze
GAZE_AWAY_THRESHOLD = 0.30          # definite look away

# === AGGRESSIVE TIMING (user preference) ===
AWAY_CONFIRMATION_DELAY = 2.0       # seconds - require away state for this long
FOCUSED_RETURN_DELAY = 0.5          # seconds - quick restore when user returns

DIM_THRESHOLD_1 = 3.0               # seconds away → dim to 50%
DIM_LEVEL_1 = 0.5                   # brightness level

DIM_THRESHOLD_2 = 7.0               # seconds away → dim to 20%
DIM_LEVEL_2 = 0.2                   # brightness level

DISPLAY_OFF_THRESHOLD = 10.0        # seconds away → turn off display
MIN_BRIGHTNESS_BEFORE_OFF = 0.05    # minimum brightness before turning off

# === DISPLAY CONTROL ===
MIN_BRIGHTNESS = 0.05               # never go completely dark (safety)
MAX_BRIGHTNESS = 1.0                # full brightness
TRANSITION_DURATION = 1.5           # seconds for smooth brightness changes

# === CAMERA SETTINGS ===
CAMERA_DEVICE_ID = 0                # built-in webcam
CAMERA_WIDTH = 640                  # frame width (balance performance/accuracy)
CAMERA_HEIGHT = 480                 # frame height
TARGET_FPS = 30                     # target frame rate

# === STATE MANAGEMENT ===
STATE_BUFFER_SIZE = 10              # frames for median filtering
MEDIAN_FILTER_WINDOW = 10           # smooth state transitions

# === MEDIAPIPE SETTINGS ===
MEDIAPIPE_MAX_FACES = 1             # only track one face
MEDIAPIPE_REFINE_LANDMARKS = True   # enable iris tracking
MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.5
MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.5
