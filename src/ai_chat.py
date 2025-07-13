# src/ai_chat.py

"""
This module manages all interactions with the Google Gemini AI,
including API key management and the Flowey chatbot personality.
"""

import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from src.config import CONFIG_FILE, FLOWEY_SYSTEM_INSTRUCTION, LOG_FILE
from src.utils import setup_and_log

# --- Module State ---
_gemini_model = None
_api_key = None

# --- Core AI Functions ---

def log(level: str, message: str):
    """A local helper to call the main logging function with file paths."""
    setup_and_log(level, message, LOG_FILE, CONFIG_FILE)

def load_and_init_ai():
    """
    Loads the API key from config.json and initializes the Gemini model.
    """
    global _api_key, _gemini_model

    try:
        if CONFIG_FILE.exists() and CONFIG_FILE.read_text():
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                _api_key = config_data.get("api_key")
        else:
            _api_key = ""

    except (json.JSONDecodeError, IOError) as e:
        log("ERROR", f"Could not read config file at {CONFIG_FILE}: {e}")
        _api_key = None
        return False

    if not _api_key:
        log("INFO", "AI features disabled: No API key provided.")
        return False

    try:
        genai.configure(api_key=_api_key)
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
        log("INFO", "Gemini AI model initialized successfully.")
        return True

    except Exception as e:
        log("ERROR", f"Failed to initialize Gemini AI: {e}")
        _gemini_model = None
        return False

def save_api_key(key: str):
    """Saves the provided API key to config.json."""
    global _api_key
    _api_key = key
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"api_key": key}, f, indent=4)
        log("INFO", "API key saved to config file.")
    except IOError as e:
        log("ERROR", f"Could not write to config file at {CONFIG_FILE}: {e}")

def ask_flowey(prompt: str) -> str:
    """Sends a prompt to the initialized Flowey model and returns the response."""
    if not _gemini_model:
        return "Howdy! I can't talk right now. My 'soul' is missing. (AI not configured. Use 'apikey' command)."

    try:
        log("INFO", f"Sending prompt to AI: '{prompt[:50]}...'")
        response = _gemini_model.generate_content(prompt)
        log("INFO", f"AI response received: '{response.text[:50]}...'")
        return response.text

    except Exception as e:
        error_msg = f"Ugh, my head hurts... (An error occurred with the AI: {e})"
        log("ERROR", f"Gemini API error: {e}")
        return error_msg