# retro_launcher.py

"""
The main entry point for the RETRERALE Terminal Launcher.
This script initializes all subsystems and runs the main command loop.
"""

import sys
import html
import time
import subprocess
import requests

from prompt_toolkit import PromptSession, HTML, print_formatted_text
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from src.utils import clear_screen, setup_and_log
from src.config import LOG_FILE, CONFIG_FILE, LOG_DISPLAY_LINES, GAMES_DIRECTORY, SERVER_URL
from src.audio import init_audio, play_sound, stop_audio
from src.ui import (
    display_splash_screen, display_welcome_message, display_game_list,
    display_help, display_settings, display_game_info, display_drive_list,
    display_log, display_online_game_list
)
from src.game_manager import (
    GameScannerThread, update_game_lists,
    get_local_games, get_cartridge_games, get_game_map,
    find_game_by_number, detect_removable_drives
)
from src.launcher import launch_game
from src.ai_chat import load_and_init_ai, save_api_key, ask_flowey
from src.api_client import ApiClient
from src.online_manager import start_chat, stop_chat, submit_coroutine, get_chat_client

# --- Global State for Online Features ---
SERVER_PROCESS = None

def log(level: str, message: str):
    """A local helper to call the main logging function with file paths."""
    setup_and_log(level, message, LOG_FILE, CONFIG_FILE)

# --- Server Management Functions ---
def start_server():
    """Starts the backend server.py script in a subprocess."""
    global SERVER_PROCESS
    if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
        print_formatted_text(HTML("<ansiyellow>Server is already running.</ansiyellow>")); return

    server_script_path = CONFIG_FILE.parent / "server.py"
    if not server_script_path.exists():
        print_formatted_text(HTML(f"<ansired>Error: server.py not found at {server_script_path}</ansired>")); return

    try:
        print_formatted_text(HTML("<ansicyan>Starting RetroFlow server...</ansicyan>"))
        SERVER_PROCESS = subprocess.Popen([sys.executable, str(server_script_path)],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3) # Give server time to start
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print_formatted_text(HTML("<ansigreen>Server started successfully!</ansigreen>")); play_sound("menu_select")
            log("INFO", f"Server started with PID: {SERVER_PROCESS.pid}")
        else: raise Exception("Server health check failed.")
    except Exception as e:
        print_formatted_text(HTML(f"<ansired>Failed to start server: {e}</ansired>")); play_sound("error")
        log("ERROR", f"Failed to start server: {e}")
        if SERVER_PROCESS: SERVER_PROCESS.terminate(); SERVER_PROCESS = None

def stop_server():
    """Stops the backend server if it's running."""
    global SERVER_PROCESS
    if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
        print_formatted_text(HTML("<ansicyan>Stopping RetroFlow server...</ansicyan>"))
        SERVER_PROCESS.terminate(); SERVER_PROCESS.wait(timeout=5); SERVER_PROCESS = None
        print_formatted_text(HTML("<ansigreen>Server stopped.</ansigreen>")); play_sound("menu_select")
        log("INFO", "Server stopped.")
    else:
        print_formatted_text(HTML("<ansiyellow>Server is not running.</ansiyellow>"))

def main():
    """The main function that runs the entire application."""
    scanner_thread = None
    try:
        log("INFO", "--- RETRERALE Application Start ---")
        init_audio(); load_and_init_ai()
        scanner_thread = GameScannerThread(); scanner_thread.start()
        clear_screen(); play_sound("startup"); display_splash_screen()
        update_game_lists() # Perform initial blocking scan
        clear_screen(); display_welcome_message()
    except Exception as e:
        log("FATAL", f"A critical error occurred on startup: {e}")
        print(f"A fatal error occurred. Check {LOG_FILE} for details."); time.sleep(5); sys.exit(1)

    cli_style = Style.from_dict({'prompt': 'ansiblue bold'})
    api_client = ApiClient(GAMES_DIRECTORY)
    
    try:
        while True:
            # Build completer with all commands and game numbers
            static_commands = ["list", "play", "info", "scan", "drives", "ai", "apikey", "settings",
                               "log", "clear", "cls", "exit", "help", "server", "start", "stop",
                               "online", "get", "search", "chat", "connect", "disconnect", "send", "flowey", "users"]
            current_game_map = get_game_map()
            session = PromptSession(completer=WordCompleter(static_commands + list(current_game_map.keys()), ignore_case=True), style=cli_style)

            chat_client = get_chat_client()
            if chat_client and chat_client.is_connected():
                prompt_html = HTML(f"<prompt>C:\\CHAT\\{chat_client.username}> </prompt>")
            else:
                prompt_html = HTML("<prompt>C:\\RETROFLOW> </prompt>")
            
            try:
                command_line = session.prompt(prompt_html).strip()
            except (KeyboardInterrupt, EOFError): break
            if not command_line: continue

            parts = command_line.split(' ', 1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # --- Command Handling ---
            if command == 'exit': break
            elif command in ['clear', 'cls']: clear_screen(); display_welcome_message()
            elif command == 'help': clear_screen(); play_sound("menu_select"); display_help()
            elif command == 'list':
                clear_screen(); play_sound("menu_select")
                display_game_list(get_local_games(), get_cartridge_games(), get_game_map())
            elif command == 'scan':
                clear_screen(); print("Forcing a new scan..."); play_sound("scan")
                update_game_lists(); time.sleep(1); clear_screen()
                display_game_list(get_local_games(), get_cartridge_games(), get_game_map()); print("Scan complete.")
            elif command == 'play':
                if not args: print("Usage: play <number>"); play_sound("error"); continue
                game = find_game_by_number(args)
                if not game: print(f"Invalid game number: '{args}'."); play_sound("error")
                elif not game['launcher_found']: print(f"Emulator for '{game['system']}' not found."); play_sound("error")
                else:
                    success, message = launch_game(game); print(message)
                    if success: play_sound("launch_game")
                    else: play_sound("error")
            elif command == 'info':
                game = find_game_by_number(args) if args else None
                if game: clear_screen(); play_sound("menu_select"); display_game_info(game)
                else: print("Usage: info <number>"); play_sound("error")
            elif command == 'drives':
                clear_screen(); play_sound("menu_select"); display_drive_list(detect_removable_drives())
            elif command == 'ai':
                if not args: print("Usage: ai <your question>"); play_sound("error"); continue
                print("\nFlowey is thinking..."); play_sound("chat_enter"); response = ask_flowey(args)
                print_formatted_text(HTML(f"\n<ansigreen>Flowey says:</ansigreen> <ansiyellow>{html.escape(response)}</ansiyellow>"))
            elif command == 'apikey':
                new_key = input("Enter new Google AI API Key (or Enter to cancel): ").strip()
                if new_key:
                    save_api_key(new_key); print("API Key saved. Re-initializing AI..."); play_sound("menu_select")
                    if load_and_init_ai(): print("Flowey AI is now online!")
                    else: print("Failed to initialize AI with new key."); play_sound("error")
            elif command == 'settings':
                clear_screen(); play_sound("menu_select"); display_settings(SERVER_PROCESS)
            elif command == 'log':
                clear_screen(); play_sound("menu_select"); display_log(LOG_DISPLAY_LINES)
            
            # --- Online Feature Commands ---
            elif command == 'server':
                if args == 'start': start_server()
                elif args == 'stop': stop_server()
                elif args == 'scan':
                    result = api_client.request_server_scan()
                    if result:
                        added = result.get('added_count', 0)
                        print_formatted_text(HTML(f"<ansigreen>Server scan complete! Added {added} new games to the online catalog.</ansigreen>"))
                else: print("Usage: server <start|stop|scan>")
            
            elif command == 'online':
                online_parts = args.split(' ', 1)
                online_cmd = online_parts[0]
                online_args = online_parts[1] if len(online_parts) > 1 else ""
                if online_cmd == 'list':
                    games = api_client.get_games()
                    if games is not None: display_online_game_list(games, "ONLINE GAME CATALOG")
                elif online_cmd == 'search':
                    if not online_args: print("Usage: online search <query>"); continue
                    games = api_client.search_games(online_args)
                    if games is not None: display_online_game_list(games, f"ONLINE SEARCH: '{online_args}'")
                elif online_cmd == 'get':
                    if not online_args.isdigit(): print("Usage: online get <id>"); continue
                    if api_client.download_game(int(online_args)):
                        print("Run 'scan' to add it to your local list.")
                else: print("Usage: online <list|search|get>")
                
            elif command == 'chat':
                chat_parts = args.split(' ', 1)
                chat_cmd = chat_parts[0]
                chat_args = chat_parts[1] if len(chat_parts) > 1 else ""
                if chat_cmd == 'connect':
                    if not chat_args: print("Usage: chat connect <username>"); continue
                    start_chat(chat_args)
                elif chat_cmd == 'disconnect': stop_chat()
                elif chat_cmd == 'send':
                    if chat_args: submit_coroutine(get_chat_client().send_message(chat_args))
                elif chat_cmd == 'flowey':
                    if chat_args: submit_coroutine(get_chat_client().call_flowey(chat_args))
                elif chat_cmd == 'users':
                    client = get_chat_client()
                    if client and client.is_connected():
                        users = client.get_online_users()
                        print_formatted_text(HTML(f"<ansibrightwhite>Online Users ({len(users)}): {', '.join(users)}</ansibrightwhite>"))
                    else: print("Not connected to chat.")
                else: print("Usage: chat <connect|disconnect|send|flowey|users>")

            else:
                print(f"Unknown command: '{command}'. Type 'help' for a list of commands."); play_sound("error")

    finally:
        print("\nShutting down RETRERALE. Goodbye!")
        log("INFO", "--- RETRERALE Application Shutdown ---")
        stop_chat()
        stop_server()
        if scanner_thread: scanner_thread.stop(); scanner_thread.join(timeout=2)
        stop_audio()

if __name__ == "__main__":
    main()