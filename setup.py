import sys
from cx_Freeze import setup, Executable
import os

# Define the script and any necessary files (like assets, audio files, and the high score file)
script = "TetraFusion 1.3.py"
audio_folder = "Audio"
assets_folder = "assets"
high_score_file = "high_score.txt"

# Build the list of includes for cx_Freeze
includefiles = [
    (audio_folder, audio_folder),  # Include the Audio folder
    (assets_folder, assets_folder),  # Include the assets folder
    high_score_file  # Include the high score file
]

# Build the Executable
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # To prevent a terminal window from appearing

executables = [Executable(script, base=base, target_name="TetraFusion 1.3.exe")]

# Setup function for cx_Freeze
setup(
    name="TetraFusion",
    version="1.3",
    description="TetraFusion made by Wayne",
    options={
        "build_exe": {
            "packages": ["pygame", "random", "sys", "os"],
            "include_files": includefiles,
            "include_msvcr": True  # Ensures necessary runtime files are included
        }
    },
    executables=executables
)
