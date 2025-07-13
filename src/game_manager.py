# src/game_manager.py

"""
Manages game discovery, including scanning local folders and removable
"cartridge" drives. It runs in a background thread to keep the UI responsive.
"""

import os
import psutil
import platform
import threading
import time
from pathlib import Path

from src.config import (
    EMULATOR_PROFILES, EMULATORS_DIRECTORY, GAMES_DIRECTORY,
    MIN_DRIVE_SIZE_MB, SCAN_INTERVAL_SECONDS, LOG_FILE, CURRENT_PLATFORM
)
from src.utils import log_message

# --- Module State (Private) ---
# These are the true, live lists that the background thread updates.
_local_games = []
_cartridge_games = {}
_game_map = {}
_scan_lock = threading.Lock()

# --- Public Getter Functions (The Fix) ---
# These functions provide safe, thread-locked access to the current game state.

def get_local_games() -> list:
    with _scan_lock:
        return _local_games[:] # Return a copy

def get_cartridge_games() -> dict:
    with _scan_lock:
        return _cartridge_games.copy()

def get_game_map() -> dict:
    with _scan_lock:
        return _game_map.copy()

def find_game_by_number(num_str: str) -> dict | None:
    """Safely finds a game's info dictionary by its display number."""
    with _scan_lock:
        return _game_map.get(num_str)

# --- Game Discovery (Internal) ---

def _find_emulator_executable(emulator_folder_name: str) -> Path | None:
    emu_path = EMULATORS_DIRECTORY / emulator_folder_name
    if not emu_path.is_dir(): return None
    for item in emu_path.iterdir():
        if item.is_file():
            if CURRENT_PLATFORM == "Windows" and item.suffix.lower() == '.exe': return item
            elif CURRENT_PLATFORM in ["Linux", "Darwin"] and os.access(item, os.X_OK): return item
    return None

def _discover_games_in_path(base_path: Path) -> list:
    found_games = []
    if not base_path.is_dir(): return found_games
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            file_path = Path(root) / filename
            ext = file_path.suffix.lower()
            if ext in EMULATOR_PROFILES:
                profile = EMULATOR_PROFILES[ext]
                emulator_exe = _find_emulator_executable(profile['emulator_folder'])
                game_info = {
                    'name': file_path.stem, 'path': file_path, 'system': profile['system'],
                    'profile': profile, 'launcher_found': emulator_exe is not None,
                    'emulator_exe': emulator_exe
                }
                found_games.append(game_info)
    return sorted(found_games, key=lambda g: g['name'])

def detect_removable_drives() -> list[Path]:
    """Detects and returns a list of removable drives, filtering by size."""
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
                log_message("WARNING", f"Could not access drive {partition.mountpoint}: {e}", LOG_FILE)
                continue
    return removable_drives

# --- Main Update and Threading Logic ---

def update_game_lists():
    """The main scanning function that updates the internal game state."""
    global _local_games, _cartridge_games, _game_map
    log_message("DEBUG", "Starting game list update scan.", LOG_FILE)

    new_local_games = _discover_games_in_path(GAMES_DIRECTORY)
    new_cartridge_games = {}
    for drive_path in detect_removable_drives():
        drive_id = f"{drive_path.name} ({str(drive_path)})"
        new_cartridge_games[drive_id] = _discover_games_in_path(drive_path)

    new_game_map = {}
    game_number = 1
    for game in new_local_games:
        new_game_map[str(game_number)] = game
        game_number += 1
    for drive_id in sorted(new_cartridge_games.keys()):
        for game in new_cartridge_games[drive_id]:
            new_game_map[str(game_number)] = game
            game_number += 1

    with _scan_lock:
        _local_games = new_local_games
        _cartridge_games = new_cartridge_games
        _game_map = new_game_map
    log_message("INFO", f"Scan complete. Mapped {len(_game_map)} total games.", LOG_FILE)

class GameScannerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()

    def run(self):
        log_message("INFO", "Background game scanner thread started.", LOG_FILE)
        while not self.stop_event.is_set():
            update_game_lists()
            self.stop_event.wait(SCAN_INTERVAL_SECONDS)
        log_message("INFO", "Background game scanner thread stopped.", LOG_FILE)

    def stop(self):
        self.stop_event.set()