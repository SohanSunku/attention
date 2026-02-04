#!/usr/bin/env python3
"""Test keyboard-based brightness control"""

import sys
sys.path.insert(0, '/Users/sohan/dev/attention')

from attention_monitor.display.brightness_controller import BrightnessController
import time

print("Testing keyboard-based brightness control...")
print("Watch your screen brightness change!\n")

controller = BrightnessController()

if not controller.available:
    print("✗ Brightness controller not available")
    sys.exit(1)

print("✓ Brightness controller initialized")
print(f"  Current brightness: {controller.current_brightness:.2f}\n")

# Test dimming
print("Test 1: Dimming to 50%...")
controller.set_brightness(0.5)
time.sleep(2)

print("Test 2: Dimming to 20%...")
controller.set_brightness(0.2)
time.sleep(2)

print("Test 3: Dimming to minimum (5%)...")
controller.set_brightness(0.05)
time.sleep(2)

print("Test 4: Restoring to 100%...")
controller.set_brightness(1.0)
time.sleep(1)

print("\n✓ All tests complete!")
print("If your screen brightness changed during the test, it's working!")
