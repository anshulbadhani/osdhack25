# retro_launcher.py

"""
The main entry point for the RETRERALE Terminal Launcher.
This script initializes all subsystems and runs the main command loop.
"""

import html
import time
from prompt_toolkit import PromptSession, HTML, print_formatted_text
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from src.utils import clear_screen, log_message
from src.config import LOG_FILE, CONFIG_FILE, GAMES_DIRECTORY, EMULATORS_DIRECTORY, SOUNDS_DIRECTORY
from src.audio import init_audio, play_sound, stop_audio
from src.ui import (
    display_splash_screen, display_welcome_message, display_game_list,
    display_help, display_settings, display_game_info, display_drive_list
)
from src.game_manager import (
    GameScannerThread, update_game_lists,
    get_local_games, get_cartridge_games, get_game_map,
    find_game_by_number, detect_removable_drives
)
from src.launcher import launch_game
from src.ai_chat import load_and_init_ai, save_api_key, ask_flowey

def main():
    """The main function that runs the entire application."""
    
    GAMES_DIRECTORY.mkdir(exist_ok=True)
    EMULATORS_DIRECTORY.mkdir(exist_ok=True)
    SOUNDS_DIRECTORY.mkdir(exist_ok=True)
    LOG_FILE.touch(exist_ok=True)
    CONFIG_FILE.touch(exist_ok=True)
    
    log_message("INFO", "--- RETRERALE Application Start ---", LOG_FILE)
    
    init_audio()
    load_and_init_ai()
    
    scanner_thread = GameScannerThread()
    scanner_thread.start()
    
    clear_screen()
    play_sound("startup")
    display_splash_screen()
    
    print("Performing initial scan...")
    update_game_lists()
    
    clear_screen()
    display_welcome_message()

    cli_style = Style.from_dict({'prompt': 'ansiblue bold'})
    static_commands = [
        "list", "play", "info", "scan", "drives", "ai",
        "apikey", "settings", "log", "clear", "cls", "exit", "help"
    ]
    session = PromptSession(style=cli_style)

    try:
        while True:
            # Always get the latest game map for the completer
            current_game_map = get_game_map()
            dynamic_completer = WordCompleter(static_commands + list(current_game_map.keys()), ignore_case=True)
            session.completer = dynamic_completer

            try:
                command_line = session.prompt(HTML("\n<prompt>C:\\RETROFLOW> </prompt>")).strip().lower()
            except (KeyboardInterrupt, EOFError):
                break

            if not command_line: continue

            parts = command_line.split(' ', 1)
            command = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            # --- Command Handling ---
            
            if command == 'exit':
                break

            elif command in ['clear', 'cls']:
                clear_screen(); display_welcome_message()

            elif command == 'help':
                clear_screen(); play_sound("menu_select"); display_help()

            elif command == 'list':
                clear_screen(); play_sound("menu_select")
                display_game_list(get_local_games(), get_cartridge_games(), get_game_map())

            elif command == 'scan':
                clear_screen(); print("Forcing a new scan for all games..."); play_sound("scan")
                update_game_lists(); time.sleep(1); clear_screen()
                display_game_list(get_local_games(), get_cartridge_games(), get_game_map())
                print("Scan complete.")

            elif command == 'play':
                if not args: print("Usage: play <number>"); play_sound("error"); continue
                game_to_play = find_game_by_number(args)
                if not game_to_play: print(f"Invalid game number: '{args}'."); play_sound("error")
                elif not game_to_play['launcher_found']: print(f"Emulator for '{game_to_play['system']}' not found."); play_sound("error")
                else:
                    success, message = launch_game(game_to_play); print(message)
                    if success: play_sound("launch_game"); time.sleep(2); clear_screen(); display_welcome_message()
                    else: play_sound("error")

            elif command == 'info':
                if not args: print("Usage: info <number>"); play_sound("error"); continue
                game_to_show = find_game_by_number(args)
                if game_to_show:
                    clear_screen(); play_sound("menu_select"); display_game_info(game_to_show)
                else:
                    print(f"Invalid game number: '{args}'."); play_sound("error")

            elif command == 'drives':
                clear_screen(); play_sound("menu_select")
                drives = detect_removable_drives()
                display_drive_list(drives)

            elif command == 'ai':
                if not args: print("Usage: ai <your question>"); play_sound("error"); continue
                print("\nFlowey is thinking..."); play_sound("chat_enter"); response = ask_flowey(args)
                print_formatted_text(HTML(f"\n<ansigreen>Flowey says:</ansigreen> <ansiyellow>{html.escape(response)}</ansiyellow>"))

            elif command == 'apikey':
                clear_screen(); print("Get a free Google AI API key from: https://aistudio.google.com/app/apikey")
                new_key = input("Enter new API Key (or press Enter to cancel): ").strip()
                if new_key:
                    save_api_key(new_key); print("API Key saved. Re-initializing AI..."); play_sound("menu_select")
                    if load_and_init_ai(): print("Flowey AI is now online!")
                    else: print("Failed to initialize AI with the new key."); play_sound("error")
                else: print("API key update cancelled.")
                time.sleep(2); clear_screen(); display_welcome_message()
            
            elif command == 'settings':
                clear_screen(); play_sound("menu_select"); display_settings()

            else:
                print(f"Unknown command: '{command}'. Type 'help' for a list of commands."); play_sound("error")

    finally:
        print("\nShutting down RETRERALE. Goodbye!")
        log_message("INFO", "--- RETRERALE Application Shutdown ---", LOG_FILE)
        scanner_thread.stop()
        scanner_thread.join(timeout=2)
        stop_audio()

if __name__ == "__main__":
    main()