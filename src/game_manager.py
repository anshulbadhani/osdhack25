# src/game_manager.py

"""
Manages game discovery, including scanning local folders and removable
"cartridge" drives. It runs in a background thread to keep the UI responsive.
"""

import os
import psutil
import shutil
import platform
import threading
import time
from pathlib import Path

from src.config import (
    EMULATOR_PROFILES, EMULATORS_DIRECTORY, GAMES_DIRECTORY,
    MIN_DRIVE_SIZE_MB, SCAN_INTERVAL_SECONDS, LOG_FILE, CONFIG_FILE, CURRENT_PLATFORM
)
from src.utils import setup_and_log

# --- Module State (Private) ---
_local_games = []
_cartridge_games = {}
_game_map = {}
_scan_lock = threading.Lock()

# --- Local Logging Helper ---
def log(level: str, message: str):
    """A local helper to call the main logging function with file paths."""
    setup_and_log(level, message, LOG_FILE, CONFIG_FILE)

# --- Public Getter Functions ---
def get_local_games() -> list:
    with _scan_lock: return _local_games[:]
def get_cartridge_games() -> dict:
    with _scan_lock: return _cartridge_games.copy()
def get_game_map() -> dict:
    with _scan_lock: return _game_map.copy()
def find_game_by_number(num_str: str) -> dict | None:
    with _scan_lock: return _game_map.get(num_str)

# --- Game Discovery (Internal) ---

def find_emulator_path(emulator_command: str) -> Path | None:
    """
    Finds the path to an emulator using a multi-layered search strategy.

    1.  Checks for a local, portable version in 'Emulators/<command>/'.
    2.  If not found, checks if the command exists in the system's PATH.

    Args:
        emulator_command (str): The command name of the emulator (e.g., "fceux").

    Returns:
        A Path object to the executable, or None if not found anywhere.
    """
    # --- Priority 1: Check for a local, portable executable ---
    local_emu_path = EMULATORS_DIRECTORY / emulator_command
    if local_emu_path.is_dir():
        for item in local_emu_path.iterdir():
            if item.is_file():
                if CURRENT_PLATFORM == "Windows" and item.suffix.lower() == '.exe':
                    log("DEBUG", f"Found local emulator for '{emulator_command}' at: {item}")
                    return item
                # On macOS, a portable .app can be placed here.
                elif CURRENT_PLATFORM == "Darwin" and item.suffix.lower() == '.app':
                    log("DEBUG", f"Found local .app for '{emulator_command}' at: {item}")
                    return item
                # On Linux, a portable AppImage or binary can be placed here.
                elif CURRENT_PLATFORM == "Linux" and os.access(item, os.X_OK):
                    log("DEBUG", f"Found local executable for '{emulator_command}' at: {item}")
                    return item

    # --- Priority 2: Check the system's PATH ---
    # shutil.which() is the standard Python way to find an executable in the PATH.
    system_path = shutil.which(emulator_command)
    if system_path:
        log("DEBUG", f"Found system-installed emulator for '{emulator_command}' at: {system_path}")
        return Path(system_path)

    # --- If not found anywhere ---
    log("WARNING", f"Emulator command '{emulator_command}' could not be found locally or in system PATH.")
    return None

def _find_emulator_executable(emulator_folder_name: str) -> Path | None:
    emu_path = EMULATORS_DIRECTORY / emulator_folder_name
    if not emu_path.is_dir(): return None
    for item in emu_path.iterdir():
        if item.is_file():
            if CURRENT_PLATFORM == "Windows" and item.suffix.lower() == '.exe': return item
            elif CURRENT_PLATFORM in ["Linux", "Darwin"] and os.access(item, os.X_OK): return item
    return None

def _discover_games_in_path(base_path: Path) -> list:
    """
    Scans a given path and all its subdirectories for supported game files.
    """
    found_games = []
    if not base_path.is_dir(): return found_games
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            file_path = Path(root) / filename
            ext = file_path.suffix.lower()
            if ext in EMULATOR_PROFILES:
                profile = EMULATOR_PROFILES[ext]
                # *** THIS LINE IS UPDATED ***
                emulator_exe = find_emulator_path(profile['command']) # Use the new function

                game_info = {
                    'name': file_path.stem, 'path': file_path, 'system': profile['system'],
                    'profile': profile, 'launcher_found': emulator_exe is not None,
                    'emulator_exe': emulator_exe
                }
                found_games.append(game_info)
    return sorted(found_games, key=lambda g: g['name'])

def detect_removable_drives() -> list[Path]:
    removable_drives = []
    min_size_bytes = MIN_DRIVE_SIZE_MB * 1024 * 1024
    for partition in psutil.disk_partitions(all=False):
        is_removable = 'removable' in partition.opts.lower() or \
                       (platform.system() == "Darwin" and partition.mountpoint.startswith('/Volumes/')) or \
                       (platform.system() == "Linux" and partition.mountpoint.startswith('/media/'))
        if is_removable:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                if usage.total > min_size_bytes:
                    removable_drives.append(Path(partition.mountpoint))
            except (FileNotFoundError, PermissionError) as e:
                log("WARNING", f"Could not access drive {partition.mountpoint}: {e}")
                continue
    return removable_drives

# --- Main Update and Threading Logic ---
def update_game_lists():
    global _local_games, _cartridge_games, _game_map
    log("DEBUG", "Starting game list update scan.")
    new_local_games = _discover_games_in_path(GAMES_DIRECTORY)
    new_cartridge_games = {}
    for drive_path in detect_removable_drives():
        drive_id = f"{drive_path.name} ({str(drive_path)})"
        new_cartridge_games[drive_id] = _discover_games_in_path(drive_path)
    new_game_map = {}; game_number = 1
    for game in new_local_games:
        new_game_map[str(game_number)] = game; game_number += 1
    for drive_id in sorted(new_cartridge_games.keys()):
        for game in new_cartridge_games[drive_id]:
            new_game_map[str(game_number)] = game; game_number += 1
    with _scan_lock:
        _local_games = new_local_games
        _cartridge_games = new_cartridge_games
        _game_map = new_game_map
    log("INFO", f"Scan complete. Mapped {len(_game_map)} total games.")

class GameScannerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True); self.stop_event = threading.Event()
    def run(self):
        log("INFO", "Background game scanner thread started.")
        while not self.stop_event.is_set():
            update_game_lists(); self.stop_event.wait(SCAN_INTERVAL_SECONDS)
        log("INFO", "Background game scanner thread stopped.")
    def stop(self):
        self.stop_event.set()
