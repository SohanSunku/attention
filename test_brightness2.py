#!/usr/bin/env python3
"""Test brightness control with error details"""

try:
    from Quartz import CoreGraphics as CG
    import ctypes
    import ctypes.util

    print("✓ PyObjC imported successfully")

    # Get main display
    display_id = CG.CGMainDisplayID()
    print(f"✓ Display ID: {display_id}")

    # Check if this is a built-in display
    print(f"  Is builtin: {CG.CGDisplayIsBuiltin(display_id)}")
    print(f"  Is main: {CG.CGDisplayIsMain(display_id)}")

    # Try using CoreGraphics library directly
    print("\nTrying to access brightness via ctypes...")
    cg_lib = ctypes.CDLL(ctypes.util.find_library('CoreGraphics'))

    # Set up function signatures
    cg_lib.CGDisplayGetBrightness.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
    cg_lib.CGDisplayGetBrightness.restype = ctypes.c_int

    brightness = ctypes.c_float()
    result = cg_lib.CGDisplayGetBrightness(display_id, ctypes.byref(brightness))

    print(f"  Result code: {result}")

    if result == 0:
        print(f"✓ Current brightness: {brightness.value:.2f}")
    elif result == -536870201:  # kCGErrorIllegalArgument
        print("✗ Built-in display brightness control not supported via CGDisplay API")
        print("  This is normal on Apple Silicon Macs")
        print("\nAlternative: Use AppleScript or IOKit")
    else:
        print(f"✗ Error code: {result}")
        print("  May need Accessibility permissions")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
