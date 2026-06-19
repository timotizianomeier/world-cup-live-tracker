"""
Renders the ⚽ emoji at 1024×1024 using macOS AppKit (Apple Color Emoji font)
and converts it to icon.icns via iconutil.

AppKit is available inside the build venv because py2app depends on pyobjc.
"""

import shutil
import subprocess
import sys
from pathlib import Path

SIZE = 1024


def render_emoji(size: int, out_png: Path) -> None:
    try:
        from AppKit import (
            NSImage, NSBitmapImageRep, NSAttributedString,
            NSFont, NSColor, NSBezierPath, NSFontAttributeName,
        )
        from Foundation import NSMakeRect, NSMakeSize, NSMakePoint
    except ImportError:
        sys.exit(
            "pyobjc-framework-Cocoa not found. "
            "It is installed automatically when you run build.sh."
        )

    img = NSImage.alloc().initWithSize_(NSMakeSize(size, size))
    img.lockFocus()

    # Transparent background (macOS adds the rounded-square mask automatically)
    NSColor.clearColor().set()
    NSBezierPath.fillRect_(NSMakeRect(0, 0, size, size))

    # Render ⚽ with Apple Color Emoji
    font_size = size * 0.88
    font = (
        NSFont.fontWithName_size_("Apple Color Emoji", font_size)
        or NSFont.systemFontOfSize_(font_size)
    )
    attr_str = NSAttributedString.alloc().initWithString_attributes_(
        "⚽", {NSFontAttributeName: font}
    )
    text_size = attr_str.size()
    x = (size - text_size.width) / 2.0
    y = (size - text_size.height) / 2.0
    attr_str.drawAtPoint_(NSMakePoint(x, y))

    img.unlockFocus()

    # Export PNG (type 4 = NSBitmapImageFileTypePNG)
    bmp = NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
    png_data = bmp.representationUsingType_properties_(4, {})
    png_data.writeToFile_atomically_(str(out_png), True)
    print(f"  Saved {out_png}")


def make_icns(png: Path, icns: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow not installed. Run: pip install pillow")

    iconset = png.parent / "icon.iconset"
    iconset.mkdir(exist_ok=True)
    img = Image.open(png).convert("RGBA")

    for s in [16, 32, 64, 128, 256, 512, 1024]:
        img.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
        if s <= 512:
            img.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")

    result = subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(icns)],
        capture_output=True,
    )
    shutil.rmtree(iconset)
    if result.returncode != 0:
        sys.exit(f"iconutil error: {result.stderr.decode()}")
    print(f"  Saved {icns}")


if __name__ == "__main__":
    base = Path(__file__).parent
    png = base / "icon.png"
    icns = base / "icon.icns"

    print("Rendering ⚽ emoji with Apple Color Emoji…")
    render_emoji(SIZE, png)

    print("Converting to .icns…")
    make_icns(png, icns)

    print("Done.")
