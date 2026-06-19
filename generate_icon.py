"""
Generate a 1024x1024 football icon (icon.png) and convert it to icon.icns
using macOS iconutil. Run this script before py2app.
"""

import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow not installed. Run: pip install pillow")


SIZE = 1024
BALL_RADIUS = 430
CX, CY = SIZE // 2, SIZE // 2


def draw_football(size: int = SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    scale = size / SIZE
    r = int(BALL_RADIUS * scale)
    cx, cy = size // 2, size // 2

    # White ball body
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))

    # Shadow — subtle grey arc at bottom-right
    shadow_r = int(r * 0.92)
    draw.ellipse(
        [cx - shadow_r + int(20 * scale), cy - shadow_r + int(20 * scale),
         cx + shadow_r + int(20 * scale), cy + shadow_r + int(20 * scale)],
        fill=(210, 210, 210, 80),
    )

    # Black pentagon patches — classic football pattern
    # Central pentagon at top, surrounded by 5 pentagons
    patch_color = (30, 30, 30, 255)
    patch_scale = r / 430.0

    def pentagon(cx_p, cy_p, radius, rotation_deg=0):
        """Return list of (x,y) for a regular pentagon."""
        pts = []
        for i in range(5):
            angle = math.radians(rotation_deg + 72 * i - 90)
            pts.append((
                cx_p + radius * math.cos(angle),
                cy_p + radius * math.sin(angle),
            ))
        return pts

    pent_r = int(85 * patch_scale)   # pentagon circumradius
    gap = int(185 * patch_scale)     # dist from ball centre to patch centre

    # Centre patch (rotated so flat side faces up)
    centre_pts = pentagon(cx, cy, pent_r, rotation_deg=0)
    draw.polygon(centre_pts, fill=patch_color)

    # 5 surrounding patches, each rotated ~36° relative to centre
    for i in range(5):
        angle = math.radians(72 * i - 90)
        px = cx + gap * math.cos(angle)
        py = cy + gap * math.sin(angle)
        # Outer pentagons are rotated so a vertex points toward the centre
        rot = 72 * i - 90 + 180
        pts = pentagon(px, py, pent_r, rotation_deg=rot)
        draw.polygon(pts, fill=patch_color)

    # Seam lines connecting centre patch to each outer patch
    seam_width = max(2, int(8 * patch_scale))
    for i in range(5):
        angle = math.radians(72 * i - 90)
        # From edge of centre patch to inner edge of outer patch
        x1 = cx + pent_r * math.cos(angle)
        y1 = cy + pent_r * math.sin(angle)
        x2 = cx + (gap - pent_r) * math.cos(angle)
        y2 = cy + (gap - pent_r) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=patch_color, width=seam_width)

    # Outer circle border
    border_w = max(3, int(12 * patch_scale))
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=(30, 30, 30, 255),
        width=border_w,
    )

    return img


def make_icns(png_path: Path, icns_path: Path):
    """Build a .icns file from a 1024x1024 PNG using macOS iconutil."""
    iconset = png_path.parent / "icon.iconset"
    iconset.mkdir(exist_ok=True)

    img = Image.open(png_path).convert("RGBA")

    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for s in sizes:
        resized = img.resize((s, s), Image.LANCZOS)
        resized.save(iconset / f"icon_{s}x{s}.png")
        if s <= 512:
            resized2 = img.resize((s * 2, s * 2), Image.LANCZOS)
            resized2.save(iconset / f"icon_{s}x{s}@2x.png")

    result = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)],
        capture_output=True,
    )
    shutil.rmtree(iconset)

    if result.returncode != 0:
        print("iconutil error:", result.stderr.decode())
        sys.exit(1)


if __name__ == "__main__":
    base = Path(__file__).parent
    png_path = base / "icon.png"
    icns_path = base / "icon.icns"

    print("Drawing football icon…")
    img = draw_football(SIZE)
    img.save(png_path)
    print(f"  Saved {png_path}")

    print("Converting to .icns…")
    make_icns(png_path, icns_path)
    print(f"  Saved {icns_path}")
    print("Done.")
