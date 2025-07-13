# src/audio.py

"""
This module manages all audio playback for the RetroFlow application
using the pygame.mixer library for non-blocking sound.
"""

import pygame.mixer as mixer
from pathlib import Path

from src.config import SOUNDS_DIRECTORY, SOUND_FILES, LOG_FILE, CONFIG_FILE
from src.utils import setup_and_log # <-- FIX: Import the correct function name

# A global flag to track if the audio system was successfully initialized
_mixer_initialized = False

def log(level: str, message: str):
    """A local helper to call the main logging function with file paths."""
    setup_and_log(level, message, LOG_FILE, CONFIG_FILE)

def init_audio():
    """
    Initializes the pygame mixer.
    """
    global _mixer_initialized
    if _mixer_initialized:
        return

    try:
        mixer.init()
        _mixer_initialized = True
        log("INFO", "Audio system initialized successfully.")
    except Exception as e:
        _mixer_initialized = False
        log("ERROR", f"Failed to initialize audio system: {e}")

def play_sound(sound_key: str):
    """
    Plays a sound effect based on its key from the SOUND_FILES mapping.
    """
    if not _mixer_initialized:
        return

    sound_filename = SOUND_FILES.get(sound_key)
    if not sound_filename:
        log("WARNING", f"Sound key '{sound_key}' not found in configuration.")
        return

    sound_path = SOUNDS_DIRECTORY / sound_filename
    if not sound_path.is_file():
        log("WARNING", f"Sound file for key '{sound_key}' not found at: {sound_path}")
        return

    try:
        sound = mixer.Sound(str(sound_path))
        sound.play()
        log("DEBUG", f"Played sound: '{sound_key}'")
    except Exception as e:
        log("ERROR", f"Could not play sound '{sound_key}': {e}")

def stop_audio():
    """
    Stops all playing sounds and quits the mixer.
    """
    if _mixer_initialized:
        mixer.quit()
        log("INFO", "Audio system shut down.")