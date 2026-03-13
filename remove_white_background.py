#!/usr/bin/env python3
"""
Script to remove white background from images and make them transparent.
Usage: python remove_white_background.py input_image.png output_image.png
"""

from PIL import Image
import sys
import os


def remove_white_background(input_path, output_path, threshold=240):
    """
    Remove white background from an image and save with transparency.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image (should be .png)
        threshold: Pixel brightness threshold (0-255). Pixels brighter than this become transparent.
    """
    # Open the image
    img = Image.open(input_path)
    
    # Convert to RGBA if not already
    img = img.convert("RGBA")
    
    # Get pixel data
    data = img.getdata()
    
    # Create new pixel data with transparency
    new_data = []
    for item in data:
        # If pixel is white-ish (all RGB values above threshold), make it transparent
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            # Make pixel fully transparent
            new_data.append((255, 255, 255, 0))
        else:
            # Keep original pixel
            new_data.append(item)
    
    # Update image data
    img.putdata(new_data)
    
    # Save the result
    img.save(output_path, "PNG")
    print(f"✓ Background removed successfully!")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python remove_white_background.py input_image.png [output_image.png] [threshold]")
        print("\nOptions:")
        print("  input_image.png   - Path to input image")
        print("  output_image.png  - Path to output image (default: input_name_no_bg.png)")
        print("  threshold         - Brightness threshold 0-255 (default: 240)")
        print("\nExample:")
        print("  python remove_white_background.py device.png device_transparent.png 235")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Default output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_no_bg.png"
    
    # Optional threshold parameter
    threshold = int(sys.argv[3]) if len(sys.argv) >= 4 else 240
    
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found!")
        sys.exit(1)
    
    remove_white_background(input_path, output_path, threshold)


if __name__ == "__main__":
    main()
