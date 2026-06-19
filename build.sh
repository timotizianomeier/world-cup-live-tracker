#!/usr/bin/env bash
set -euo pipefail

VENV=".venv"

echo "==> Setting up Python build environment…"
rm -rf "$VENV"
if command -v uv &>/dev/null; then
    # Use uv to create the venv; prefer Python 3.12
    uv venv --python 3.12 "$VENV"
    export VIRTUAL_ENV="$PWD/$VENV"
    INSTALL_CMD="uv pip install"
else
    # Fall back to whichever Python 3.x is available
    PYTHON_BIN=""
    for try in python3.12 python3.11 python3; do
        if command -v "$try" &>/dev/null; then PYTHON_BIN="$try"; break; fi
    done
    [ -z "$PYTHON_BIN" ] && { echo "❌  Python 3 not found. Install from https://www.python.org/downloads/"; exit 1; }
    "$PYTHON_BIN" -m venv "$VENV"
    INSTALL_CMD="$VENV/bin/pip install"
fi

PYTHON="$VENV/bin/python"

echo ""
echo "==> Installing dependencies…"
$INSTALL_CMD rumps requests python-dateutil pillow py2app

echo ""
echo "==> Patching py2app for frozen-zlib Python builds (uv/standalone CPython)…"
# py2app tries to copy zlib.__file__ but uv's CPython compiles zlib as a built-in
# (no __file__). The patch makes the copy conditional, which is safe on all Pythons.
"$PYTHON" - << 'PYEOF'
import pathlib, zlib, sys
if hasattr(zlib, "__file__"):
    print("  zlib is a .so — no patch needed")
    sys.exit(0)
for p in pathlib.Path(".venv").rglob("build_app.py"):
    if "py2app" not in str(p):
        continue
    old = "self.copy_file(zlib.__file__, os.path.dirname(arcdir))"
    new = "if hasattr(zlib, '__file__'): self.copy_file(zlib.__file__, os.path.dirname(arcdir))"
    txt = p.read_text()
    if old in txt:
        p.write_text(txt.replace(old, new))
        print(f"  Patched {p}")
    else:
        print(f"  Already patched or line not found in {p}")
PYEOF

echo ""
echo "==> Generating football icon…"
"$PYTHON" generate_icon.py

echo ""
echo "==> Building WorldCupBar.app…"
rm -rf build dist
"$PYTHON" setup.py py2app 2>&1 | grep -v "^ADD INFO\|^copying file\|^--- Skipping\|^CTYPES USERS"

echo ""
echo "✅  Built: dist/WorldCupBar.app"
echo ""
echo "Next steps:"
echo "  • Open immediately:   open dist/WorldCupBar.app"
echo "  • Move to /Applications (optional, for Spotlight):"
echo "      cp -r dist/WorldCupBar.app /Applications/"
echo "  • Auto-launch at login:"
echo "      System Settings → General → Login Items → add WorldCupBar.app"
