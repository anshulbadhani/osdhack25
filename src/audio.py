# src/audio.py

"""
This module manages all audio playback for the RetroFlow application
using the pygame.mixer library for non-blocking sound.
"""

import pygame.mixer as mixer
from pathlib import Path

# Import configurations and utilities from our other modules
from src.config import SOUNDS_DIRECTORY, SOUND_FILES, LOG_FILE
from src.utils import log_message

# A global flag to track if the audio system was successfully initialized
_mixer_initialized = False

def init_audio():
    """
    Initializes the pygame mixer.
    This should be called once at the start of the application.
    """
    global _mixer_initialized
    if _mixer_initialized:
        return

    try:
        mixer.init()
        _mixer_initialized = True
        log_message("INFO", "Audio system initialized successfully.", LOG_FILE)
    except Exception as e:
        _mixer_initialized = False
        log_message("ERROR", f"Failed to initialize audio system: {e}", LOG_FILE)
        # We don't print to the console here to keep the startup clean.
        # The user will simply experience a silent application.

def play_sound(sound_key: str):
    """
    Plays a sound effect based on its key from the SOUND_FILES mapping.

    Args:
        sound_key (str): The key corresponding to the sound to play (e.g., 'startup', 'error').
    """
    if not _mixer_initialized:
        return  # Do nothing if the audio system isn't working

    sound_filename = SOUND_FILES.get(sound_key)
    if not sound_filename:
        log_message("WARNING", f"Sound key '{sound_key}' not found in configuration.", LOG_FILE)
        return

    sound_path = SOUNDS_DIRECTORY / sound_filename
    if not sound_path.is_file():
        log_message("WARNING", f"Sound file for key '{sound_key}' not found at: {sound_path}", LOG_FILE)
        return

    try:
        sound = mixer.Sound(str(sound_path))
        sound.play()
        log_message("DEBUG", f"Played sound: '{sound_key}'", LOG_FILE)
    except Exception as e:
        log_message("ERROR", f"Could not play sound '{sound_key}': {e}", LOG_FILE)

def stop_audio():
    """
    Stops all playing sounds and quits the mixer.
    Should be called when the application exits.
    """
    if _mixer_initialized:
        mixer.quit()
        log_message("INFO", "Audio system shut down.", LOG_FILE)