#!/usr/bin/env python3
"""Create a simple app icon for ResearchTool."""
import subprocess
import os

# Icon sizes required for macOS
sizes = [16, 32, 64, 128, 256, 512, 1024]

# Create base icon using CoreGraphics via Python (or just create colored squares)
# For simplicity, we'll create a gradient icon using sips from a base image

# First create a simple SVG-like representation as text then convert
base_size = 1024

# Create a simple PNG using ImageMagick if available, or use Python PIL
try:
    # Try using ImageMagick
    subprocess.run([
        "convert", "-size", f"{base_size}x{base_size}",
        "gradient:#4A90D9-#1E3A5F",  # Blue gradient
        "-gravity", "center",
        "-fill", "white",
        "-font", "SF-Pro-Bold",
        "-pointsize", "500",
        "-annotate", "0", "R",
        "icon_1024x1024@1x.png"
    ], check=True)
except FileNotFoundError:
    # Fallback: create solid color square using sips
    # First create a simple colored image
    print("ImageMagick not found, creating simple icon...")
    os.system(f'''
        # Create a simple blue square using Python and PIL or raw bytes
        python3 -c "
import struct
import zlib

def create_png(size, filename):
    # Create a simple blue gradient PNG
    width = height = size
    
    def make_pixel_data():
        rows = []
        for y in range(height):
            row = []
            for x in range(width):
                # Blue gradient from top-left to bottom-right
                r = int(30 + (x/width) * 40)  # 30-70
                g = int(58 + (y/height) * 80)  # 58-138  
                b = int(95 + ((x+y)/(width+height)) * 120)  # 95-215
                a = 255
                row.extend([r, g, b, a])
            rows.append(bytes([0] + row))  # 0 = no filter
        return b''.join(rows)
    
    def png_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
    
    signature = b'\\x89PNG\\r\\n\\x1a\\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    pixel_data = make_pixel_data()
    compressed = zlib.compress(pixel_data, 9)
    
    with open(filename, 'wb') as f:
        f.write(signature)
        f.write(png_chunk(b'IHDR', ihdr))
        f.write(png_chunk(b'IDAT', compressed))
        f.write(png_chunk(b'IEND', b''))

create_png({base_size}, 'icon_1024x1024@1x.png')
print('Created base icon')
"
    ''')

print("Base icon created")
