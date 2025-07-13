# src/ai_chat.py

"""
This module manages all interactions with the Google Gemini AI,
including API key management and the Flowey chatbot personality.
"""

import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Import configurations and utilities from our other modules
from src.config import CONFIG_FILE, FLOWEY_SYSTEM_INSTRUCTION, LOG_FILE
from src.utils import log_message

# --- Module State ---
_gemini_model = None
_api_key = None

# --- Core AI Functions ---

def load_and_init_ai():
    """
    Loads the API key from config.json and initializes the Gemini model.
    This should be called at application startup.

    Returns:
        bool: True if AI was initialized successfully, False otherwise.
    """
    global _api_key, _gemini_model

    # 1. Load the API key
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                _api_key = config_data.get("api_key")
        else:
            # If config.json doesn't exist, create it with an empty key.
            save_api_key("")
            _api_key = ""

    except (json.JSONDecodeError, IOError) as e:
        log_message("ERROR", f"Could not read config file at {CONFIG_FILE}: {e}", LOG_FILE)
        _api_key = None
        return False

    # 2. Initialize the model if a key exists
    if not _api_key:
        log_message("INFO", "AI features disabled: No API key provided.", LOG_FILE)
        return False

    try:
        genai.configure(api_key=_api_key)
        
        # Configure safety settings to be less restrictive for a character like Flowey
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        _gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=FLOWEY_SYSTEM_INSTRUCTION,
            safety_settings=safety_settings
        )
        log_message("INFO", "Gemini AI model initialized successfully.", LOG_FILE)
        return True

    except Exception as e:
        log_message("ERROR", f"Failed to initialize Gemini AI: {e}", LOG_FILE)
        _gemini_model = None
        return False

def save_api_key(key: str):
    """
    Saves the provided API key to config.json.
    """
    global _api_key
    _api_key = key
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"api_key": key}, f, indent=4)
        log_message("INFO", "API key saved to config file.", LOG_FILE)
    except IOError as e:
        log_message("ERROR", f"Could not write to config file at {CONFIG_FILE}: {e}", LOG_FILE)

def ask_flowey(prompt: str) -> str:
    """
    Sends a prompt to the initialized Flowey model and returns the response.
    """
    if not _gemini_model:
        return "Howdy! I can't talk right now. My 'soul' is missing. (AI not configured. Use the 'apikey' command to set a key)."

    try:
        log_message("INFO", f"Sending prompt to AI: '{prompt[:50]}...'", LOG_FILE)
        # For a one-off question, generate_content is simpler than start_chat
        response = _gemini_model.generate_content(prompt)
        log_message("INFO", f"AI response received: '{response.text[:50]}...'", LOG_FILE)
        return response.text

    except Exception as e:
        error_msg = f"Ugh, my head hurts... (An error occurred with the AI: {e})"
        log_message("ERROR", f"Gemini API error: {e}", LOG_FILE)
        return error_msg