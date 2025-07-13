# src/config.py

"""
This module contains all the configuration settings, paths, and constants
for the RetroFlow Terminal Launcher. All paths are defined relative to the
project root, which is outside the 'dist' folder.
"""

import platform
from pathlib import Path
from src.utils import get_project_root

# --- Core Paths ---
PROJECT_ROOT = get_project_root()
GAMES_DIRECTORY = PROJECT_ROOT / "Games"
EMULATORS_DIRECTORY = PROJECT_ROOT / "Emulators"
SOUNDS_DIRECTORY = PROJECT_ROOT / "Sounds"
CONFIG_FILE = PROJECT_ROOT / "config.json"
LOG_FILE = PROJECT_ROOT / "retroflow.log"

# --- Online Features ---
SERVER_URL = "http://localhost:8000"

# --- Platform ---
CURRENT_PLATFORM = platform.system()  # 'Windows', 'Darwin' (macOS), or 'Linux'

# --- Emulator Profiles ---
EMULATOR_PROFILES = {
    # Nintendo
    '.nes': {'command': 'fceux', 'system': 'Nintendo Entertainment System', 'args': []},
    '.smc': {'command': 'snes9x', 'system': 'Super Nintendo', 'args': []},
    '.sfc': {'command': 'snes9x', 'system': 'Super Nintendo', 'args': []},
    '.gb':  {'command': 'mgba', 'system': 'Game Boy', 'args': []},
    '.gbc': {'command': 'mgba', 'system': 'Game Boy Color', 'args': []},
    '.gba': {'command': 'mgba', 'system': 'Game Boy Advance', 'args': []},
    '.n64': {'command': 'project64', 'system': 'Nintendo 64', 'args': []},
    '.z64': {'command': 'mupen64plus', 'system': 'Nintendo 64', 'args': []},
    '.nds': {'command': 'desmume', 'system': 'Nintendo DS', 'args': []}, # Added NDS

    # Sega
    '.md':  {'command': 'gens', 'system': 'Sega Genesis', 'args': []},
    '.gen': {'command': 'gens', 'system': 'Sega Genesis', 'args': []},

    # Sony
    '.ps1': {'command': 'epsxe', 'system': 'PlayStation', 'args': []},
    '.bin': {'command': 'epsxe', 'system': 'PlayStation', 'args': []},

    # PC / Other
    '.wad': {'command': 'gzdoom', 'system': 'Doom Engine', 'args': ['-iwad']},
    '.exe': {'command': 'dosbox', 'system': 'MS-DOS', 'args': ['-exit']},
}

# --- Sound File Configuration ---
SOUND_FILES = {
    "startup": "startup.mp3", "launch_game": "launch.mp3", "error": "error.mp3",
    "menu_select": "select.mp3", "chat_enter": "chat.mp3", "scan": "scan.mp3",
}

# --- AI Chatbot Configuration ---
FLOWEY_SYSTEM_INSTRUCTION = (
    "You are Flowey the Flower from Undertale, now serving as a retro gaming assistant in a DOS-like terminal. "
    "You maintain your manipulative, sarcastic personality but are genuinely helpful with gaming advice. "
    "You have extensive knowledge of retro games, emulators, and gaming history. "
    "You can be condescending but ultimately want the user to succeed at gaming. "
    "Reference classic games, gaming culture, and occasionally break the fourth wall. "
    "Keep responses concise but personality-rich. You're fascinated by the user's 'DETERMINATION' to play old games. "
    "Sometimes mock modern gaming while praising retro classics."
)

# --- Application Behavior Settings ---
SCAN_INTERVAL_SECONDS = 30
MIN_DRIVE_SIZE_MB = 100
LOG_DISPLAY_LINES = 25