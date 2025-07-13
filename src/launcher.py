# src/launcher.py

"""
This module handles the execution of external game emulators.
It constructs and runs the appropriate command-line process.
"""

import subprocess
from pathlib import Path

# Import configurations and utilities from our other modules
from src.utils import log_message
from src.config import LOG_FILE, CURRENT_PLATFORM

def launch_game(game_info: dict) -> tuple[bool, str]:
    """
    Launches the selected game using its configured emulator in a non-blocking process.

    Args:
        game_info (dict): The dictionary containing all info about the game,
                          including 'emulator_exe', 'path', and 'profile'.

    Returns:
        A tuple containing:
        - bool: True if the launch command was sent successfully, False otherwise.
        - str: A message for the user indicating success or the specific error.
    """
    emulator_path = game_info.get('emulator_exe')
    game_path = game_info.get('path')
    profile = game_info.get('profile')
    game_name = game_info.get('name', 'Unknown Game')

    if not all([emulator_path, game_path, profile]):
        error_msg = f"Incomplete game info provided for {game_name}."
        log_message("ERROR", f"Launch failed: {error_msg}", LOG_FILE)
        return False, error_msg

    # --- Construct the Command ---
    cmd = []
    
    # Special handling for macOS .app bundles, which need to be opened differently.
    if CURRENT_PLATFORM == "Darwin" and str(emulator_path).endswith(".app"):
        # The 'open' command is used to launch .app bundles on macOS.
        # '--args' passes subsequent items as arguments to the application itself.
        cmd = ['open', '-a', str(emulator_path), '--args']
    else:
        # For Windows .exe and Linux executables, the path is the command.
        cmd = [str(emulator_path)]

    # Add any special arguments defined in the emulator's profile (e.g., -iwad for Doom).
    cmd.extend(profile.get('args', []))
    
    # Finally, add the path to the game file itself.
    cmd.append(str(game_path))

    log_message("INFO", f"Attempting to launch with command: {' '.join(cmd)}", LOG_FILE)

    # --- Execute the Command ---
    try:
        # Use subprocess.Popen to launch the game in a new process.
        # This is non-blocking, so our terminal app doesn't freeze.
        subprocess.Popen(cmd)
        
        success_msg = f"Launching {game_name}..."
        log_message("INFO", f"Successfully sent launch command for {game_name}.", LOG_FILE)
        return True, success_msg
        
    except FileNotFoundError:
        error_msg = f"Emulator not found at path: {emulator_path}"
        log_message("ERROR", f"Launch failed: {error_msg}", LOG_FILE)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"An OS error occurred while launching: {e}"
        log_message("ERROR", f"Launch failed: {error_msg} | Command: {' '.join(cmd)}", LOG_FILE)
        return False, error_msg