# src/utils.py

"""
This module provides core utility functions for the RetroFlow application,
such as path resolution, screen clearing, logging, and initial setup.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """
    Finds the absolute path to the project's root folder.

    - When running as a script (`.py`), it returns the directory containing 'retro_launcher.py'.
    - When running as a frozen executable (`.exe`) inside a 'dist' folder,
      it navigates up one level to find the directory containing 'dist',
      ensuring it can find sibling folders like 'Games' and 'Emulators'.
    """
    if getattr(sys, 'frozen', False):
        # We are in a PyInstaller bundle. sys.executable is the path to the .exe.
        # We want the parent of the directory containing the .exe (e.g., parent of 'dist').
        return Path(sys.executable).resolve().parent.parent
    else:
        # We are running as a script. This file is in 'src/'.
        # The project root is one level up.
        return Path(__file__).resolve().parent.parent

def clear_screen():
    """Clears the terminal screen in an OS-independent way."""
    os.system('cls' if os.name == 'nt' else 'clear')

def setup_and_log(level: str, message: str, log_file_path: Path, config_file_path: Path):
    """
    Ensures log/config files exist and writes a timestamped message.
    This consolidated function is called for every log event.
    """
    try:
        # Ensure the essential config and log files exist before trying to write.
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_file_path.exists():
            config_file_path.touch()
        
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_file_path.exists():
            log_file_path.touch()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except IOError as e:
        print(f"CRITICAL: Could not write to log file at {log_file_path}. Error: {e}")
        print(f"LOG ATTEMPT: {message}")