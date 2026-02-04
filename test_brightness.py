#!/usr/bin/env python3
"""Test brightness control"""

try:
    from Quartz import CoreGraphics as CG
    print("✓ PyObjC imported successfully")

    # Get main display
    display_id = CG.CGMainDisplayID()
    print(f"✓ Display ID: {display_id}")

    # Try to get brightness
    err, brightness = CG.CGDisplayGetBrightness(display_id)
    print(f"  Error code: {err}")
    print(f"  Brightness: {brightness}")

    if err == 0:
        print(f"✓ Current brightness: {brightness:.2f}")

        # Try to set brightness
        print("\nTrying to set brightness to 0.5...")
        err = CG.CGDisplaySetBrightness(display_id, 0.5)
        print(f"  Set brightness error code: {err}")

        if err == 0:
            print("✓ Brightness control working!")
        else:
            print("✗ Failed to set brightness - needs Accessibility permissions")
    else:
        print("✗ Failed to get brightness - needs Accessibility permissions")
        print("\nPlease enable Accessibility for Terminal:")
        print("System Settings → Privacy & Security → Accessibility → Enable Terminal")

except ImportError as e:
    print(f"✗ PyObjC not available: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
