from setuptools import setup

APP = ["worldcupbar.py"]

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "icon.icns",
    "packages": ["rumps", "requests", "dateutil"],
    "plist": {
        "LSUIElement": True,                          # hide from Dock
        "CFBundleName": "WorldCupBar",
        "CFBundleDisplayName": "World Cup Bar",
        "CFBundleIdentifier": "com.timo.worldcupbar",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "© 2026 Timo",
    },
}

setup(
    name="WorldCupBar",
    app=APP,
    options={"py2app": OPTIONS},
)
