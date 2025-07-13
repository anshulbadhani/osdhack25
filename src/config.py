# src/config.py

"""
This module contains all the configuration settings, paths, and constants
for the RetroFlow Terminal Launcher.
"""

import platform
from pathlib import Path

# Import the root-finding utility from our utils module
from src.utils import get_project_root

# --- Core Paths ---
# This logic ensures that paths work correctly whether running from a script
# or a PyInstaller-built .exe.
PROJECT_ROOT = get_project_root()
GAMES_DIRECTORY = PROJECT_ROOT / "Games"
EMULATORS_DIRECTORY = PROJECT_ROOT / "Emulators"
SOUNDS_DIRECTORY = PROJECT_ROOT / "Sounds"
CONFIG_FILE = PROJECT_ROOT / "config.json" # Storing config in the root for simplicity
LOG_FILE = PROJECT_ROOT / "retroflow.log"

# --- Platform ---
CURRENT_PLATFORM = platform.system()  # 'Windows', 'Darwin' (macOS), or 'Linux'

# --- Emulator Profiles ---
# This dictionary is the heart of the game launching system.
# It maps a file extension to the required emulator's FOLDER name and launch arguments.
# The launcher will then find the actual executable within that folder.
# This approach is OS-independent and flexible.
#
# 'emulator_folder': The name of the subfolder inside the 'Emulators' directory.
# 'system': The full name of the console for display purposes.
# 'args': A list of command-line arguments to pass to the emulator BEFORE the game path.
#         Example for Doom: ['-iwad'] results in 'gzdoom.exe -iwad doom.wad'

EMULATOR_PROFILES = {
    # Nintendo
    '.nes': {'emulator_folder': 'fceux', 'system': 'Nintendo Entertainment System', 'args': []},
    '.smc': {'emulator_folder': 'snes9x', 'system': 'Super Nintendo', 'args': []},
    '.sfc': {'emulator_folder': 'snes9x', 'system': 'Super Nintendo', 'args': []},
    '.gb':  {'emulator_folder': 'mgba', 'system': 'Game Boy', 'args': []},
    '.gbc': {'emulator_folder': 'mgba', 'system': 'Game Boy Color', 'args': []},
    '.gba': {'emulator_folder': 'mgba', 'system': 'Game Boy Advance', 'args': []},
    '.n64': {'emulator_folder': 'project64', 'system': 'Nintendo 64', 'args': []},
    '.z64': {'emulator_folder': 'project64', 'system': 'Nintendo 64', 'args': []},

    # Sega
    '.md':  {'emulator_folder': 'gens', 'system': 'Sega Genesis', 'args': []},
    '.gen': {'emulator_folder': 'gens', 'system': 'Sega Genesis', 'args': []},

    # Sony
    '.ps1': {'emulator_folder': 'epsxe', 'system': 'PlayStation', 'args': []},
    '.bin': {'emulator_folder': 'epsxe', 'system': 'PlayStation', 'args': []}, # Often used with .cue files

    # PC / Other
    '.wad': {'emulator_folder': 'gzdoom', 'system': 'Doom Engine', 'args': ['-iwad']},
    # For DOSBox, we might want the game to be the first argument.
    # The launcher logic will handle argument placement.
    '.exe': {'emulator_folder': 'dosbox', 'system': 'MS-DOS', 'args': ['-exit']},
}

# --- Sound File Configuration ---
# Maps an event name to a sound file in the 'Sounds' directory.
SOUND_FILES = {
    "startup": "startup.mp3",
    "launch_game": "launch.mp3",
    "error": "error.mp3",
    "menu_select": "select.mp3",
    "chat_enter": "chat.mp3",
    "scan": "scan.mp3",
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
SCAN_INTERVAL_SECONDS = 30      # How often to check for new/removed cartridges.
MIN_DRIVE_SIZE_MB = 100         # Minimum size for a drive to be considered a "cartridge".
LOG_DISPLAY_LINES = 25          # Number of log lines to show with the 'log' command.