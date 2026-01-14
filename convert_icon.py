"""Convert PNG icon to ICO format for Windows."""
from PIL import Image
import os

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
png_path = os.path.join(script_dir, "icon.png")
ico_path = os.path.join(script_dir, "icon.ico")

# Check if PNG exists, if not try the generated one
if not os.path.exists(png_path):
    # Try the generated icon
    brain_dir = r"C:\Users\admin\.gemini\antigravity\brain\68dd6787-73b8-43ea-9bb4-c9c4692da368"
    for f in os.listdir(brain_dir):
        if f.startswith("danz_app_icon") and f.endswith(".png"):
            png_path = os.path.join(brain_dir, f)
            break

if os.path.exists(png_path):
    print(f"Converting {png_path} to {ico_path}")
    img = Image.open(png_path)
    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    # Resize to standard icon sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"Created {ico_path}")
else:
    print(f"PNG not found at {png_path}")
