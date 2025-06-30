#!/usr/bin/env python3

from PIL import Image
import os

def convert_icon():
    # Input and output paths
    input_path = '../flightpath/assets/icons/icon.icns'  # or whatever your source file is
    output_path = '../flightpath/assets/icons/icon.ico'
    
    try:
        # Open the source image
        with Image.open(input_path) as img:
            # Convert to ICO format
            img.save(output_path, format='ICO')
            print(f"✅ Successfully converted {input_path} to {output_path}")
            
    except FileNotFoundError:
        print(f"❌ Error: Could not find {input_path}")
        print("Please check the path and filename.")
        
    except Exception as e:
        print(f"❌ Error converting icon: {e}")

if __name__ == "__main__":
    convert_icon()