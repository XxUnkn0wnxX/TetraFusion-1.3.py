import sys
import os
import re
import shutil
from cx_Freeze import setup, Executable

# Remove the existing build folder if it exists.
build_folder = "build"
if os.path.exists(build_folder):
    try:
        shutil.rmtree(build_folder)
        print(f"Deleted existing '{build_folder}' folder.")
    except Exception as e:
        print(f"Warning: could not delete '{build_folder}' folder: {e}")

# Check if we are building a DMG (for macOS)
is_dmg = any("bdist_dmg" in arg for arg in sys.argv)

# Read the version from TetraFusion.py.
version = "0.0.0"  # Default version if not found
with open("TetraFusion.py", "r") as f:
    for line in f:
        match = re.search(r'#\s*Game Ver:\s*([\d\.]+)', line)
        if match:
            version = match.group(1)
            break

# Determine the executable extension based on platform and build command.
if sys.platform == "win32":
    exe_extension = ".exe"
elif sys.platform == "darwin":
    # For macOS: if building a DMG, the app bundle should have no extension;
    # otherwise (e.g. in the build folder) use .exe to match the default naming.
    exe_extension = "" if is_dmg else ".exe"
else:
    # For Linux, no extension.
    exe_extension = ""

exe_name = f"TetraFusion {version}{exe_extension}"

# Include additional files (assets, audio, etc.)
include_files = [
    ("assets", "assets"),
    ("Audio", "Audio"),
    "high_score.txt",
    "ICON1.ico",
    "LICENSE.txt",
]

# On Windows, use the Win32 GUI base.
base = "Win32GUI" if sys.platform == "win32" else None
exe = Executable(
    script="TetraFusion.py",
    base=base,
    target_name=exe_name,
    icon="ICON1.ico",  # Set the application icon
)

# Configure MSI options and shortcuts only for Windows.
if sys.platform == "win32":
    shortcut_table = [
        ("DesktopShortcut",     # Shortcut
         "DesktopFolder",       # Directory_
         f"TetraFusion {version}",  # Shortcut name
         "TARGETDIR",           # Component_
         f"[TARGETDIR]{exe_name}",  # Target executable
         None,  # Arguments
         None,  # Description
         None,  # Hotkey
         None,  # Icon
         None,  # IconIndex
         None,  # ShowCmd
         "TARGETDIR",  # Working directory
         )
    ]
    msi_data = {"Shortcut": shortcut_table}
    bdist_msi_options = {
        "data": msi_data,
        "upgrade_code": "{E1234567-1234-5678-1234-56789ABCDEF0}",  # Replace with a unique GUID
    }
else:
    bdist_msi_options = {}

# Setup configuration.
setup(
    name="TetraFusion",
    version=version,
    description="A Tetris-inspired game with custom features",
    options={
        "build_exe": {
            "include_files": include_files,
            "includes": ["pygame"],
        },
        "bdist_msi": bdist_msi_options,
    },
    executables=[exe],
)
