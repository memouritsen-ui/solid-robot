#!/usr/bin/env python3
"""Resize base icon to all required sizes."""
import subprocess
import os
import shutil

# Required sizes for macOS iconset
sizes = [
    (16, 1), (16, 2),
    (32, 1), (32, 2),
    (128, 1), (128, 2),
    (256, 1), (256, 2),
    (512, 1), (512, 2)
]

base_icon = "icon_1024x1024@1x.png"
iconset_dir = "AppIcon.iconset"

if not os.path.exists(base_icon):
    print(f"Error: {base_icon} not found")
    exit(1)

for size, scale in sizes:
    actual_size = size * scale
    suffix = f"@{scale}x" if scale > 1 else ""
    filename = f"{iconset_dir}/icon_{size}x{size}{suffix}.png"
    
    # Use sips to resize
    subprocess.run([
        "sips", "-z", str(actual_size), str(actual_size),
        base_icon, "--out", filename
    ], capture_output=True)
    print(f"Created {filename}")

print("All icon sizes created")
