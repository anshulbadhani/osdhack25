# src/utils.py

"""
This module provides core utility functions for the RetroFlow application,
such as path resolution, screen clearing, and logging.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# --- Core Utility Functions ---

def get_project_root() -> Path:
    """
    Finds the absolute path to the project's root folder.

    This is the key function for PyInstaller compatibility. It ensures that
    whether running as a script (`.py`) or a frozen executable (`.exe`),
    the application can find external folders like 'Games' and 'Emulators'.

    - When running as a script, it returns the directory of the script.
    - When running as a frozen .exe inside a 'dist' folder, it navigates
      up one level to find the parent directory where the .exe resides.
      This allows us to place 'Games', 'Emulators', etc., next to the .exe.
    """
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (e.g., PyInstaller .exe).
        # The executable is at sys.executable.
        # We want the directory *containing* the executable.
        return Path(sys.executable).resolve().parent
    else:
        # We are running in a normal Python environment.
        # The main script is in the project root.
        # We go up one level from this file's location (src/).
        return Path(__file__).resolve().parent.parent

def clear_screen():
    """Clears the terminal screen in an OS-independent way."""
    os.system('cls' if os.name == 'nt' else 'clear')

def log_message(level: str, message: str, log_file_path: Path):
    """
    Writes a timestamped message to the specified log file.

    Args:
        level (str): The severity level of the message (e.g., 'INFO', 'ERROR').
        message (str): The log message content.
        log_file_path (Path): The Path object pointing to the log file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except IOError:
        # If logging fails, we print to console as a fallback but don't crash.
        print(f"CRITICAL: Could not write to log file at {log_file_path}")
        print(f"LOG ATTEMPT: {log_entry}")