# src/launcher.py

"""
This module handles the execution of external game emulators.
It constructs and runs the appropriate command-line process.
"""

import subprocess
from pathlib import Path

from src.utils import setup_and_log # <-- FIX: Import the correct function name
from src.config import LOG_FILE, CONFIG_FILE, CURRENT_PLATFORM

def log(level: str, message: str):
    """A local helper to call the main logging function with file paths."""
    setup_and_log(level, message, LOG_FILE, CONFIG_FILE)

def launch_game(game_info: dict) -> tuple[bool, str]:
    """
    Launches the selected game using its configured emulator in a non-blocking process.
    """
    emulator_path = game_info.get('emulator_exe')
    game_path = game_info.get('path')
    profile = game_info.get('profile')
    game_name = game_info.get('name', 'Unknown Game')

    if not all([emulator_path, game_path, profile]):
        error_msg = f"Incomplete game info provided for {game_name}."
        log("ERROR", f"Launch failed: {error_msg}")
        return False, error_msg

    cmd = []
    
    if CURRENT_PLATFORM == "Darwin" and str(emulator_path).endswith(".app"):
        cmd = ['open', '-a', str(emulator_path), '--args']
    else:
        cmd = [str(emulator_path)]

    cmd.extend(profile.get('args', []))
    cmd.append(str(game_path))

    log("INFO", f"Attempting to launch with command: {' '.join(cmd)}")

    try:
        subprocess.Popen(cmd)
        success_msg = f"Launching {game_name}..."
        log("INFO", f"Successfully sent launch command for {game_name}.")
        return True, success_msg
        
    except FileNotFoundError:
        error_msg = f"Emulator not found at path: {emulator_path}"
        log("ERROR", f"Launch failed: {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"An OS error occurred while launching: {e}"
        log("ERROR", f"Launch failed: {error_msg} | Command: {' '.join(cmd)}")
        return False, error_msg