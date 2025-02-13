import sys
import os
import re
import shutil
from cx_Freeze import setup, Executable, build_exe as _build_exe

# If no command is provided, default based on the OS.
# This will auto-select the proper build command if the user runs "python3 setup.py" without arguments.
if len(sys.argv) == 1:
    if sys.platform.startswith("win"):
        sys.argv.append("bdist_msi")
    elif sys.platform == "darwin":
        sys.argv.append("bdist_dmg")
    elif sys.platform.startswith("linux"):
        sys.argv.append("build_linux")

# Custom build command that moves settings.py into the build folder.
class CustomBuildExe(_build_exe):
    def run(self):
        # Run the standard build_exe process.
        super().run()
        # Determine the build directory used by cx_Freeze.
        build_dir = self.build_exe
        settings_path = "settings.py"
        if os.path.exists(settings_path):
            dest_path = os.path.join(build_dir, "settings.py")
            try:
                shutil.move(settings_path, dest_path)
                print(f"Moved '{settings_path}' to '{dest_path}'")
            except Exception as e:
                print(f"Warning: Could not move '{settings_path}' into build folder: {e}")

# Remove the existing build folder if it exists.
build_folder = "build"
if os.path.exists(build_folder):
    try:
        shutil.rmtree(build_folder)
        print(f"Deleted existing '{build_folder}' folder.")
    except Exception as e:
        print(f"Warning: could not delete '{build_folder}' folder: {e}")

# Ensure high_score.txt exists and is empty.
with open("high_score.txt", "w") as f:
    pass

# Check if we are building a DMG (for macOS)
is_dmg = any("bdist_dmg" in arg for arg in sys.argv)

# Read the first line from TetraFusion.py to extract version.
with open("TetraFusion.py", "r") as f:
    first_line = f.readline().strip()
match = re.search(r'#\s*Game Ver:?\s*([\d\.]+)', first_line)
version = match.group(1) if match else "0.0.0"

# Determine the executable extension based on platform and build command.
if sys.platform.startswith("win"):
    exe_extension = ".exe"
elif sys.platform == "darwin":
    # For macOS: if building a DMG, the app bundle should have no extension.
    exe_extension = "" if is_dmg else ".exe"
else:
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
base = "Win32GUI" if sys.platform.startswith("win") else None
exe = Executable(
    script="TetraFusion.py",
    base=base,
    target_name=exe_name,
    icon="ICON1.ico",  # Set the application icon
)

# Configure MSI options and shortcuts only for Windows.
if sys.platform.startswith("win"):
    # Define the shortcut table for the MSI installer.
    shortcut_table = [
        ("DesktopShortcut",     # Shortcut
         "DesktopFolder",       # Directory_
         f"TetraFusion {version}",  # Shortcut name
         "TARGETDIR",           # Component_
         f"[TARGETDIR]{exe_name}",  # Target executable
         None,  # Arguments
         None,  # Description
         None,  # Hotkey
         None,  # Icon (explicit icon reference removed)
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

# For Linux, register a new command name "build_linux" that uses our custom build class.
cmdclass = {}
if sys.platform.startswith("linux"):
    class BuildLinux(CustomBuildExe):
         description = "Build executable for Linux"
    cmdclass["build_linux"] = BuildLinux
else:
    # For non-Linux platforms, use the standard build_exe command.
    cmdclass["build_exe"] = CustomBuildExe

# Setup configuration.
setup(
    name="TetraFusion",
    version=version,
    description="A Tetris-inspired game with custom features",
    options={
        # The build options apply to the command that will be run.
        ("build_exe" if not sys.platform.startswith("linux") else "build_linux"): {
            "include_files": include_files,
            "includes": ["pygame", "mutagen"],  # Include necessary Python modules (module inclusions updated)
        },
        "bdist_msi": bdist_msi_options,
    },
    executables=[exe],
    cmdclass=cmdclass,
)
