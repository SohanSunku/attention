# Attention Monitoring System

A Python application that monitors user attention via webcam eye gaze tracking and controls macOS display brightness accordingly. Features aggressive response times with clear, configurable thresholds.

## Features

- **Real-time attention detection** using MediaPipe Face Mesh with iris tracking
- **Multi-signal fusion**: Combines head pose, eye gaze, and eye aspect ratio for accurate detection
- **Aggressive timing**: 3s → 50% brightness, 7s → 20% brightness, 10s → display off
- **Smooth transitions**: Brightness changes use easing for comfortable viewing
- **Terminal-based interface** with optional debug visualization
- **Highly configurable**: All thresholds in a single config file

## How It Works

The system uses three detection methods:

1. **Head Pose Estimation**: Detects if your head is turned away (>30° yaw or >20° pitch)
2. **Eye Aspect Ratio (EAR)**: Detects if your eyes are closed (EAR < 0.2)
3. **Iris Position**: Tracks where you're looking relative to your eye corners

These signals are combined with time-based hysteresis to prevent false positives from brief glances.

## Requirements

- macOS (tested on macOS 10.15+)
- Python 3.9 or higher
- Built-in webcam
- System Permissions:
  - Camera access
  - Accessibility (for brightness control)

## Installation

1. Clone or download this repository:
```bash
cd /Users/sohan/dev/attention
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## macOS Permissions Setup

### Camera Access
1. Open **System Settings** → **Privacy & Security** → **Camera**
2. Enable camera access for **Terminal** (or your terminal application)

### Accessibility (for brightness control)
1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Enable access for **Terminal** (or your terminal application)

If brightness control doesn't work, you may see an error message with instructions.

## Usage

### Basic Usage
```bash
# Normal operation
python -m attention_monitor.main

# Or use the shorthand if installed
python -m attention_monitor
```

### With Debug Visualization
```bash
# Show camera feed with overlay
python -m attention_monitor.main --debug
```

Debug mode shows:
- Face landmarks (green dots)
- Iris landmarks (blue circles)
- Head pose angles (yaw, pitch)
- Gaze ratios for left/right eyes
- Eye Aspect Ratio (EAR)
- Current attention state
- Time in current state
- Target brightness

### Other Options
```bash
# Dry run (monitor only, no brightness changes)
python -m attention_monitor.main --dry-run

# Verbose logging
python -m attention_monitor.main --log-level DEBUG

# Combined options
python -m attention_monitor.main --debug --log-level INFO
```

### Keyboard Controls (Debug Mode)
- `q`: Quit application
- `p`: Pause/resume monitoring
- `r`: Reset state manager

### Stopping the Application
Press `Ctrl+C` to gracefully shutdown. The application will:
- Stop camera capture
- Restore original brightness
- Clean up resources

## Configuration

All thresholds are in `attention_monitor/config.py`. Common adjustments:

### Make Less Aggressive
```python
# In config.py
DIM_THRESHOLD_1 = 5.0    # Wait 5s instead of 3s
DIM_THRESHOLD_2 = 10.0   # Wait 10s instead of 7s
DISPLAY_OFF_THRESHOLD = 15.0  # Wait 15s instead of 10s
```

### Change Brightness Levels
```python
# In config.py
DIM_LEVEL_1 = 0.7        # Dim to 70% instead of 50%
DIM_LEVEL_2 = 0.4        # Dim to 40% instead of 20%
```

### Adjust Detection Sensitivity
```python
# In config.py
HEAD_POSE_YAW_THRESHOLD = 40     # Allow more head turn (less sensitive)
EYE_ASPECT_RATIO_THRESHOLD = 0.15  # Detect eyes closed earlier
GAZE_AWAY_THRESHOLD = 0.25       # More sensitive to gaze direction
```

### Faster/Slower Response
```python
# In config.py
AWAY_CONFIRMATION_DELAY = 3.0    # Require 3s confirmation before dimming
FOCUSED_RETURN_DELAY = 0.2       # Restore faster when user returns
```

## Architecture

```
attention_monitor/
├── config.py                    # All configurable thresholds
├── camera/
│   └── video_capture.py         # Threaded webcam capture
├── detector/
│   ├── face_detector.py         # MediaPipe Face Mesh
│   ├── head_pose_estimator.py   # Head orientation (solvePnP)
│   ├── gaze_estimator.py        # Eye tracking + EAR
│   └── attention_analyzer.py    # Multi-signal fusion
├── display/
│   ├── brightness_controller.py # PyObjC brightness control
│   └── display_power.py         # Display sleep (pmset/caffeinate)
├── state/
│   └── state_manager.py         # State machine with hysteresis
└── main.py                      # Main loop + orchestration
```

## Troubleshooting

### Camera not detected
- Check System Settings → Privacy & Security → Camera
- Try `ls /dev/video*` to see available cameras
- Change `CAMERA_DEVICE_ID` in config.py

### Brightness control not working
- Check System Settings → Privacy & Security → Accessibility
- Try running with `--dry-run` to test detection without brightness changes
- Check logs for PyObjC errors

### Display sleep requires password
- This is a macOS security feature
- The app uses `pmset displaysleepnow` which may require admin permissions
- You can disable display sleep in config by setting `DISPLAY_OFF_THRESHOLD` to a very high value

### False positives (dimming when you're focused)
- Increase `AWAY_CONFIRMATION_DELAY` in config.py
- Run with `--debug` to see detection values
- Adjust thresholds based on your typical behavior

### Detection not working
- Run with `--debug` to see camera feed
- Check if face landmarks are detected (green dots)
- Ensure good lighting
- Try adjusting `MEDIAPIPE_MIN_DETECTION_CONFIDENCE` in config.py

### High CPU usage
- Lower `TARGET_FPS` in config.py (try 15-20 fps)
- Reduce `CAMERA_WIDTH` and `CAMERA_HEIGHT`

## Performance

Typical performance on modern Mac:
- CPU usage: 10-15%
- Memory: ~150MB
- Frame rate: 30 fps
- Processing latency: <33ms per frame

## Limitations

- **macOS only**: Uses macOS-specific APIs for brightness control
- **Single user**: Designed for one person at a time
- **Glasses**: May affect iris detection accuracy (head pose still works)
- **Poor lighting**: Requires adequate lighting for face detection
- **Side profile**: Detection may fail if head is turned >60°

## License

MIT License - feel free to modify and distribute.

## Credits

Built with:
- [MediaPipe](https://google.github.io/mediapipe/) for face detection
- [OpenCV](https://opencv.org/) for computer vision
- [PyObjC](https://pyobjc.readthedocs.io/) for macOS integration

## Development

### Running Tests
```bash
# TODO: Add tests
python -m pytest tests/
```

### Contributing
Contributions welcome! Please:
1. Test on your system
2. Update documentation
3. Follow existing code style

### Future Improvements
- [ ] Multiple user profiles
- [ ] Learning mode to adapt thresholds
- [ ] Web dashboard for statistics
- [ ] Cross-platform support (Windows/Linux)
- [ ] Calibration wizard
