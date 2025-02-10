import sys
from cx_Freeze import setup, Executable

# Include additional files (assets, audio, etc.)
include_files = [
    ("assets", "assets"),
    ("Audio", "Audio"),
    "high_score.txt",
    "ICON1.ico",
    "LICENSE.txt",
]

# Define the executable target with icon specified
base = "Win32GUI" if sys.platform == "win32" else None
exe = Executable(
    script="TetraFusion 1.9.0.py",
    base=base,
    target_name="TetraFusion 1.9.0.exe",
    icon="ICON1.ico",  # Set the application icon
)

# Define the shortcut table without specifying icon or index explicitly
shortcut_table = [
    ("DesktopShortcut",  # Shortcut
     "DesktopFolder",  # Directory_
     "TetraFusion 1.9.0",  # Name of the shortcut
     "TARGETDIR",  # Component_
     "[TARGETDIR]TetraFusion 1.9.0.exe",  # Target executable
     None,  # Arguments
     None,  # Description
     None,  # Hotkey
     None,  # Icon (remove explicit icon reference)
     None,  # IconIndex
     None,  # ShowCmd
     "TARGETDIR",  # Working directory
     )
]

# Create the MSI data dictionary
msi_data = {"Shortcut": shortcut_table}

# Options for building the MSI
bdist_msi_options = {
    "data": msi_data,
    "upgrade_code": "{E1234567-1234-5678-1234-56789ABCDEF0}",  # Replace with a unique GUID
}

# Setup configuration
setup(
    name="TetraFusion",
    version="1.9.0",
    description="A Tetris-inspired game with custom features",
    options={
        "build_exe": {
            "include_files": include_files,
            "includes": ["pygame"],  # Include necessary Python modules
        },
        "bdist_msi": bdist_msi_options,
    },
    executables=[exe],
)
