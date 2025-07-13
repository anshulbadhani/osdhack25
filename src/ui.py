# src/ui.py

"""
This module handles all user interface rendering for the RETRERALE terminal,
including the splash screen, headers, game lists, and help pages.
"""

import html
from datetime import datetime
import psutil
from pathlib import Path

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from src.config import GAMES_DIRECTORY, EMULATORS_DIRECTORY, SOUNDS_DIRECTORY, CONFIG_FILE, LOG_FILE

# --- ASCII Art and Styles ---
RETRERALE_ART = FormattedText([
    ('class:ansimagenta', """
██████╗ ███████╗████████╗██████╗ ███████╗██████╗  █████╗ ██╗     ███████╗
██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██║     ██╔════╝
██████╔╝█████╗     ██║   ██████╔╝█████╗  ██████╔╝███████║██║     █████╗  
██╔══██╗██╔══╝     ██║   ██╔══██╗██╔══╝  ██╔══██╗██╔══██║██║     ██╔══╝  
██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║██║  ██║███████╗███████╗
╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
""")
])

# --- Core Display Functions ---

def display_splash_screen():
    print_formatted_text(RETRERALE_ART)
    print_formatted_text(FormattedText([('', '         '), ('class:ansigreen', 'A Dynamic, AI-Powered Retro Game Launcher')]))
    print_formatted_text(FormattedText([('', '           '), ('class:ansiyellow', 'Developed by #ifndef BROS')]))
    print(); current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print_formatted_text(FormattedText([('', '         '), ('class:ansicyan', f"Current Time: {current_time}")]))
    print_formatted_text(FormattedText([('', '         '), ('class:ansicyan', "---------------------------------")]))
    print(); print_formatted_text(FormattedText([('class:ansigreen', 'Initializing system components...')]))
    print_formatted_text(FormattedText([('class:ansiyellow', 'Scanning for local games and removable cartridges in the background...')]))
    print_formatted_text(FormattedText([('class:ansicyan', 'Please wait a moment...')]))
    print(); print_formatted_text(FormattedText([('class:ansibrightwhite', 'Press any key to continue...')]))
    input()

def display_welcome_message():
    print_formatted_text(FormattedText([('class:ansigreen', "========================================")]))
    print_formatted_text(FormattedText([('class:ansigreen', "  Welcome to Dynamic RetroFlow Terminal!  ")]))
    print_formatted_text(FormattedText([('class:ansigreen', "========================================")]))
    print_formatted_text(FormattedText([('class:ansicyan', "Type 'help' for available commands.")]))
    print_formatted_text(FormattedText([('class:ansiyellow', "Scanning for games and cartridges in the background...")]))

def display_header(title: str):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); header_width = 75
    print_formatted_text(FormattedText([('class:ansimagenta', f"┌─{'─' * (header_width-2)}─┐")]))
    print_formatted_text(FormattedText([('class:ansimagenta', '│'), ('class:ansibrightwhite', f" {title.upper():^{header_width-2}} "), ('class:ansimagenta', '│')]))
    print_formatted_text(FormattedText([('class:ansimagenta', f"├─{'─' * (header_width-2)}─┤")]))
    print_formatted_text(FormattedText([('class:ansimagenta', '│'), ('class:ansicyan', f" CURRENT SYSTEM TIME: {current_time}{'':<{header_width-26}} "), ('class:ansimagenta', '│')]))
    print_formatted_text(FormattedText([('class:ansimagenta', f"└─{'─' * (header_width-2)}─┘")])); print()

def display_game_list(local_games: list, cartridge_games: dict, game_map: dict):
    display_header("RETROFLOW GAME LIST")
    print_formatted_text(FormattedText([('class:bg:ansiblue class:ansibrightwhite', '   LOCAL GAMES   ')]))
    if not local_games:
        print_formatted_text(FormattedText([('class:ansiyellow', " No local games found in the 'Games' directory.")]))
        print_formatted_text(FormattedText([('class:ansiyellow', f" Make sure your ROMs are placed in: {str(GAMES_DIRECTORY)}")]))
    else:
        print_formatted_text(FormattedText([('class:ansibrightyellow', "  #   Game Title                           System             Status")]))
        print_formatted_text(FormattedText([('class:ansibrightyellow', "  --- ------------------------------------ ------------------ ------")]))
        for i, game in enumerate(local_games, 1):
            status_text = "READY" if game['launcher_found'] else "NO EMU"; status_color = 'class:ansigreen' if game['launcher_found'] else 'class:ansired'
            print_formatted_text(FormattedText([('class:ansibrightcyan', f"  {i:<3} "), ('class:ansiblue', f"{game['name'][:36]:<36} "), ('class:ansimagenta', f"{game['system'][:18]:<18} "), (status_color, f"{status_text:<6}")]))
    print(); num_cartridge_games = sum(len(games) for games in cartridge_games.values())
    print_formatted_text(FormattedText([('class:bg:ansiblue class:ansibrightwhite', ' CARTRIDGE GAMES ')]))
    if not num_cartridge_games:
        print_formatted_text(FormattedText([('class:ansiyellow', " No cartridge games detected.")]))
    else:
        game_idx = len(local_games)
        for drive, games_on_drive in sorted(cartridge_games.items()):
            print_formatted_text(FormattedText([('', '\n'), ('class:ansibrightyellow', f"  Drive: {drive} ({len(games_on_drive)} games)")]))
            print_formatted_text(FormattedText([('class:ansibrightyellow', "    #   Game Title                           System             Status")]))
            print_formatted_text(FormattedText([('class:ansibrightyellow', "    --- ------------------------------------ ------------------ ------")]))
            for game in games_on_drive:
                game_idx += 1; status_text = "READY" if game['launcher_found'] else "NO EMU"; status_color = 'class:ansigreen' if game['launcher_found'] else 'class:ansired'
                print_formatted_text(FormattedText([('class:ansibrightcyan', f"    {game_idx:<3} "), ('class:ansiblue', f"{game['name'][:36]:<36} "), ('class:ansimagenta', f"{game['system'][:18]:<18} "), (status_color, f"{status_text:<6}")]))
    print(); print_formatted_text(FormattedText([('class:ansigray', "="*77)])); print_formatted_text(FormattedText([('class:ansibrightwhite', f"Total Games Mapped: {len(game_map)}")]));

def display_help():
    display_header("HELP - AVAILABLE COMMANDS")
    help_text = [
        ("list", "Display the list of local and cartridge games.", "Refreshes the game display."),
        ("play <number>", "Launch a game by its number.", "Example: play 5"),
        ("info <number>", "Show detailed information about a game.", "Example: info 12"),
        ("scan", "Force an immediate scan for new games.", "Useful after adding games."),
        ("drives", "List all currently detected cartridge drives.", "Shows mount points and status."),
        ("ai <prompt>", "Ask the AI a question about games or topics.", "Example: ai what is the best nes game?"),
        ("apikey", "Set or update your Google Gemini API key.", "Required for AI features."),
        ("settings", "Display current application settings.", "Shows paths, scan intervals, etc."),
        ("log", "Display the last few entries from the log.", "Useful for debugging issues."),
        ("clear / cls", "Clear the terminal screen.", "Refreshes the display."),
        ("exit", "Exit the RetroFlow application.", "Safely shuts down the system."),
        ("help", "Display this help message.", "You are here!"),
    ]
    print_formatted_text(FormattedText([('class:ansibrightgreen', "Command Reference:")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  Command              Description                                      Usage Example")]))
    for cmd, desc, usage in help_text:
        print_formatted_text(FormattedText([('class:ansibrightcyan', f"  {cmd:<20} "), ('class:ansicyan', f"{desc:<48} "), ('class:ansiblue', f"{usage}")]))
    print(); print_formatted_text(FormattedText([('class:ansibrightwhite', "Note: Game numbers change dynamically with cartridge insertions/removals and scans.")]))

def display_settings():
    display_header("APPLICATION SETTINGS")
    settings = [
        ("Games Directory", str(GAMES_DIRECTORY)), ("Emulators Directory", str(EMULATORS_DIRECTORY)),
        ("Sounds Directory", str(SOUNDS_DIRECTORY)), ("Config File Path", str(CONFIG_FILE)),
        ("Log File Path", str(LOG_FILE)),
    ]
    print_formatted_text(FormattedText([('class:ansibrightgreen', "Current Configuration Paths:")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  Setting                           Value")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  --------------------------------- ------------------------------------------------")]))
    for setting, value in settings:
        print_formatted_text(FormattedText([('class:ansibrightcyan', f"  {setting:<33} "), ('class:ansicyan', value)]))

# --- NEW FUNCTIONS ---

def display_game_info(game_info: dict):
    """Displays detailed information for a single game."""
    display_header("GAME INFORMATION")
    
    info = {
        "Game Name": game_info.get('name', 'N/A'),
        "System": game_info.get('system', 'N/A'),
        "Full Path": str(game_info.get('path', 'N/A')),
        "Launcher Found": "Yes" if game_info.get('launcher_found') else "No",
        "Emulator Used": str(game_info.get('emulator_exe', 'N/A'))
    }
    
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  Property                  Value")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  ------------------------- ------------------------------------------------")]))
    for key, value in info.items():
        print_formatted_text(FormattedText([
            ('class:ansibrightcyan', f"  {key:<25} "),
            ('class:ansicyan', value)
        ]))

def display_drive_list(drives: list[Path]):
    """Displays a list of detected removable drives and their stats."""
    display_header("DETECTED CARTRIDGE DRIVES")
    if not drives:
        print_formatted_text(FormattedText([('class:ansiyellow', "No removable drives detected.")]))
        return

    print_formatted_text(FormattedText([('class:ansibrightyellow', "  Mount Point                  Total Size   Free Space")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  ---------------------------- ------------ ------------")]))
    for drive_path in drives:
        try:
            usage = psutil.disk_usage(str(drive_path))
            total_gb = usage.total / (1024**3)
            free_gb = usage.free / (1024**3)
            print_formatted_text(FormattedText([
                ('class:ansibrightcyan', f"  {str(drive_path)[:28]:<28} "),
                ('class:ansimagenta', f"{total_gb:<11.2f} GB "),
                ('class:ansiblue', f"{free_gb:<10.2f} GB")
            ]))
        except Exception:
            print_formatted_text(FormattedText([
                ('class:ansired', f"  {str(drive_path)[:28]:<28} ERROR: Could not read disk usage.")
            ]))