# src/online_manager.py

"""
Manages the online chat client, including its dedicated thread and asyncio event loop.
This decouples the real-time chat logic from the main application's command loop.
"""

import asyncio
import threading
import time
from prompt_toolkit import print_formatted_text, HTML

from src.config import SERVER_URL, LOG_FILE, CONFIG_FILE
from src.online_chat import OnlineChatClient
from src.utils import setup_and_log

# --- Module State ---
_chat_client = None
_chat_thread = None
_chat_loop = None

def log(level: str, message: str):
    """A local helper to call the main logging function with file paths."""
    setup_and_log(level, message, LOG_FILE, CONFIG_FILE)

def get_chat_client() -> OnlineChatClient | None:
    """Returns the current chat client instance, if it exists."""
    return _chat_client

def _run_chat_client_async(username: str):
    """
    The target function for the chat thread. It creates and manages its own
    asyncio event loop to handle the WebSocket connection.
    """
    global _chat_loop, _chat_client
    
    # Each thread must have its own event loop.
    _chat_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_chat_loop)
    
    _chat_client = OnlineChatClient(SERVER_URL, username)

    async def main_task():
        """Connects and then listens for messages."""
        if await _chat_client.connect():
            await _chat_client.listen_for_messages()
        else:
            log("ERROR", f"Chat client failed to connect for user {username}.")

    try:
        # Run the main task until it completes or is cancelled.
        _chat_loop.run_until_complete(main_task())
    except asyncio.CancelledError:
        log("INFO", "Chat task was cancelled.")
    finally:
        # Graceful shutdown of the client and loop.
        if _chat_client and _chat_client.is_connected():
            _chat_loop.run_until_complete(_chat_client.disconnect())
        
        tasks = asyncio.all_tasks(loop=_chat_loop)
        for task in tasks: task.cancel()
        group = asyncio.gather(*tasks, return_exceptions=True)
        _chat_loop.run_until_complete(group)
        _chat_loop.close()
        log("INFO", "Chat event loop has been cleanly shut down.")


def start_chat(username: str):
    """Initializes and starts the chat client and its background thread."""
    global _chat_thread
    
    if _chat_thread and _chat_thread.is_alive():
        print_formatted_text(HTML("<ansiyellow>Chat is already running or connecting.</ansiyellow>"))
        return
    
    _chat_thread = threading.Thread(target=_run_chat_client_async, args=(username,), daemon=True)
    _chat_thread.start()
    
    log("INFO", f"Chat client thread started for user {username}")
    time.sleep(2) # Give a moment for the connection attempt
    
    if not (_chat_client and _chat_client.is_connected()):
        log("WARNING", "Chat client thread started but may have failed to connect.")


def stop_chat():
    """Stops the chat client and its thread safely."""
    global _chat_thread, _chat_client, _chat_loop

    if not (_chat_thread and _chat_thread.is_alive()):
        # Don't print a message if it's already stopped.
        return
        
    print_formatted_text(HTML("<ansicyan>Disconnecting from chat...</ansicyan>"))
    
    if _chat_loop and _chat_loop.is_running():
        if _chat_client and _chat_client.is_connected():
            asyncio.run_coroutine_threadsafe(_chat_client.disconnect(), _chat_loop)
        _chat_loop.call_soon_threadsafe(_chat_loop.stop)

    _chat_thread.join(timeout=5)
    
    _chat_client = None
    _chat_thread = None
    _chat_loop = None
    print_formatted_text(HTML("<ansigreen>Disconnected from chat.</ansigreen>"))
    log("INFO", "Chat client stopped.")

def submit_coroutine(coro) -> asyncio.Future | None:
    """Helper to safely submit a coroutine to the running chat event loop."""
    if _chat_loop and _chat_client and _chat_client.is_connected():
        return asyncio.run_coroutine_threadsafe(coro, _chat_loop)
    else:
        print_formatted_text(HTML("<ansired>Not connected to chat. Use 'chat connect <user>' first.</ansired>"))
        return None