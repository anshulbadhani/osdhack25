# src/ui.py

"""
This module handles all user interface rendering for the RETRERALE terminal,
including the splash screen, headers, game lists, and help pages.
"""
import html
import re
import time
from datetime import datetime
import psutil
from pathlib import Path

from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from src.config import GAMES_DIRECTORY, EMULATORS_DIRECTORY, SOUNDS_DIRECTORY, CONFIG_FILE, LOG_FILE, SERVER_URL
from src.online_manager import get_chat_client
from src.game_manager import get_local_games, get_cartridge_games

# ASCII ART (Unchanged)
RETRERALE_ART = FormattedText([('class:ansimagenta', """
██████╗ ███████╗████████╗██████╗ ███████╗██████╗  █████╗ ██╗     ███████╗
██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██║     ██╔════╝
██████╔╝█████╗     ██║   ██████╔╝█████╗  ██████╔╝███████║██║     █████╗  
██╔══██╗██╔══╝     ██║   ██╔══██╗██╔══╝  ██╔══██╗██╔══██║██║     ██╔══╝  
██║  ██║███████╗   ██║   ██║  ██║███████╗██║  ██║██║  ██║███████╗███████╗
╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
""")])

# Core Display Functions (display_splash_screen, display_welcome_message, display_header are unchanged)
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
    print(); print_formatted_text(FormattedText([('class:ansibrightwhite', "Press any key to continue...")]))
    input()

def display_welcome_message():
    print_formatted_text(FormattedText([('class:ansigreen', "========================================")]))
    print_formatted_text(FormattedText([('class:ansigreen', "  Welcome to Dynamic RetroFlow Terminal!  ")]))
    print_formatted_text(FormattedText([('class:ansigreen', "========================================")]))
    print_formatted_text(FormattedText([('class:ansicyan', "Type 'help' for available commands.")]))
    print_formatted_text(FormattedText([('class:ansiyellow', "Scanning for games and cartridges in the background...")]))

def display_header(title: str):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_width = 75
    time_padding = header_width - len(" CURRENT SYSTEM TIME: ") - len(current_time) - 1
    print_formatted_text(FormattedText([('class:ansimagenta', f"┌─{'─' * (header_width-2)}─┐")]))
    print_formatted_text(FormattedText([('class:ansimagenta', '│'), ('class:ansibrightwhite', f" {title.upper():^{header_width-2}} "), ('class:ansimagenta', '│')]))
    print_formatted_text(FormattedText([('class:ansimagenta', f"├─{'─' * (header_width-2)}─┤")]))
    print_formatted_text(FormattedText([('class:ansimagenta', '│'), ('class:ansicyan', f" CURRENT SYSTEM TIME: {current_time}{'':<{time_padding}} "), ('class:ansimagenta', '│')]))
    print_formatted_text(FormattedText([('class:ansimagenta', f"└─{'─' * (header_width-2)}─┘")])); print()

def display_game_list(local_games: list, cartridge_games: dict, game_map: dict):
    # This function remains unchanged.
    display_header("RETROFLOW GAME LIST")
    print_formatted_text(FormattedText([('class:bg:ansiblue class:ansibrightwhite', '   LOCAL GAMES   ')]))
    if not local_games:
        print_formatted_text(FormattedText([('class:ansiyellow', f" No local games found. Place ROMs in: {str(GAMES_DIRECTORY)}")]))
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
    help_data = {
        "LOCAL COMMANDS": [
            ("list", "Display the list of local and cartridge games."),
            ("play (num)", "Launch a game by its number from the list."),
            ("info (num)", "Show detailed information about a local game."),
            ("scan", "Force a scan for local/cartridge games."),
            ("drives", "List all detected cartridge drives."),
            ("ai (prompt)", "Ask the local AI a question (Flowey)."),
        ],
        "ONLINE COMMANDS": [
            ("server start|stop", "Start or stop the backend web server."),
            ("server scan", "Tell the server to scan for new online games."),
            ("online list", "List games from the online catalog."),
            ("online search (q)", "Search the online catalog."),
            ("online get (id)", "Download a game from the catalog by its ID."),
        ],
        "CHAT COMMANDS": [
            ("chat connect (user)", "Connect to the chat server with a username."),
            ("chat disconnect", "Disconnect from the chat server."),
            ("chat send (msg)", "Send a message to the chat."),
            ("chat flowey (msg)", "Ask the chat's Flowey AI a question."),
            ("chat users", "List users currently in the chat."),
        ],
        "SYSTEM COMMANDS": [
            ("apikey", "Set your Google Gemini API key for local AI."),
            ("settings", "Display current application settings."),
            ("log", "Display the last few entries from the log."),
            ("clear / cls", "Clear the terminal screen."),
            ("exit", "Exit the RetroFlow application."),
        ]
    }
    for category, commands in help_data.items():
        print_formatted_text(HTML(f"\n<ansibrightblue>{f'--- {category} ---':^75}</ansibrightblue>"))
        print_formatted_text(HTML("<ansibrightyellow>  Command              Description</ansibrightyellow>"))
        for cmd, desc in commands:
            print_formatted_text(HTML(f"  <ansibrightcyan>{cmd:<20}</ansibrightcyan> <ansicyan>{desc}</ansicyan>"))
    print()

def display_settings(server_process):
    display_header("APPLICATION SETTINGS")
    
    # Determine server and chat status
    server_status = "Inactive"
    if server_process and server_process.poll() is None:
        server_status = f"Running (PID: {server_process.pid})"
        
    chat_client = get_chat_client()
    chat_status = "Disconnected"
    if chat_client and chat_client.is_connected():
        chat_status = f"Connected as {chat_client.username}"
    
    settings = [
        ("--- SYSTEM PATHS ---", ""),
        ("Games Directory", str(GAMES_DIRECTORY)), ("Emulators Directory", str(EMULATORS_DIRECTORY)),
        ("Config File Path", str(CONFIG_FILE)), ("Log File Path", str(LOG_FILE)),
        ("--- ONLINE FEATURES ---", ""),
        ("Server Status", server_status), ("Server URL", SERVER_URL),
        ("Chat Status", chat_status),
    ]

    for setting, value in settings:
        if "---" in setting:
            print_formatted_text(HTML(f"\n<ansibrightblue>{setting}</ansibrightblue>"))
        else:
            print_formatted_text(HTML(f"  <ansibrightcyan>{setting:<25}</ansibrightcyan> <ansicyan>{value}</ansicyan>"))
    print()

def display_online_game_list(games: list, list_title: str):
    """Displays a list of games from the online catalog."""
    display_header(list_title)
    if not games:
        print_formatted_text(HTML("<ansiyellow>No online games found or server is unavailable.</ansiyellow>"))
        return
    
    print_formatted_text(HTML("<ansibrightyellow>  ID  Game Title                         System                       Size</ansibrightyellow>"))
    print_formatted_text(HTML("<ansibrightyellow>  --- ---------------------------------- ---------------------------- --------</ansibrightyellow>"))
    for game in games:
        print_formatted_text(HTML(f"  <ansibrightcyan>{game['id']:<3}</ansibrightcyan> <ansiblue>{game['name'][:34]:<34}</ansiblue> <ansimagenta>{game['system'][:28]:<28}</ansimagenta> <ansigreen>{game['size']:<8}</ansigreen>"))
    print()

# Other UI functions (display_game_info, display_drive_list, display_log) remain unchanged.
def display_game_info(game_info: dict):
    display_header("GAME INFORMATION")
    info = {
        "Game Name": game_info.get('name', 'N/A'), "System": game_info.get('system', 'N/A'),
        "Full Path": str(game_info.get('path', 'N/A')),
        "Launcher Found": "Yes" if game_info.get('launcher_found') else "No",
        "Emulator Used": str(game_info.get('emulator_exe', 'N/A'))
    }
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  Property                  Value")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  ------------------------- ------------------------------------------------")]))
    for key, value in info.items():
        print_formatted_text(FormattedText([('class:ansibrightcyan', f"  {key:<25} "), ('class:ansicyan', value)]))

def display_drive_list(drives: list[Path]):
    display_header("DETECTED CARTRIDGE DRIVES")
    if not drives:
        print_formatted_text(FormattedText([('class:ansiyellow', "No removable drives detected.")]))
        return
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  Mount Point                  Total Size   Free Space")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  ---------------------------- ------------ ------------")]))
    for drive_path in drives:
        try:
            usage = psutil.disk_usage(str(drive_path))
            total_gb = usage.total / (1024**3); free_gb = usage.free / (1024**3)
            print_formatted_text(FormattedText([('class:ansibrightcyan', f"  {str(drive_path)[:28]:<28} "), ('class:ansimagenta', f"{total_gb:<11.2f} GB "), ('class:ansiblue', f"{free_gb:<10.2f} GB")]))
        except Exception:
            print_formatted_text(FormattedText([('class:ansired', f"  {str(drive_path)[:28]:<28} ERROR: Could not read disk usage.")]))

def display_log(num_lines: int):
    display_header("APPLICATION LOG")
    if not LOG_FILE.exists():
        print_formatted_text(FormattedText([('class:ansiyellow', "Log file not found. No entries to display.")]))
        return
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
    except Exception as e:
        print_formatted_text(FormattedText([('class:ansired', f"Error reading log file: {e}")]))
        return
    if not lines:
        print_formatted_text(FormattedText([('class:ansiyellow', "Log file is empty.")]))
        return
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  Timestamp               Level      Message")]))
    print_formatted_text(FormattedText([('class:ansibrightyellow', "  ----------------------- ---------- -------------------------------------------")]))
    level_colors = {'INFO': 'class:ansigreen', 'DEBUG': 'class:ansiblue', 'WARNING': 'class:ansiyellow', 'ERROR': 'class:ansired', 'FATAL': 'class:bg:ansired class:ansibrightwhite'}
    log_pattern = re.compile(r'^\[(.*?)\] \[(.*?)\] (.*)$')
    for line in lines[-num_lines:]:
        line = line.strip(); match = log_pattern.match(line)
        if match:
            timestamp, level, message = match.groups(); color = level_colors.get(level, 'class:ansicyan')
            print_formatted_text(FormattedText([('class:ansicyan', f"  {timestamp} "), (color, f"{level:<10} "), ('class:ansibrightwhite', html.escape(message))]))
        else:
            print_formatted_text(FormattedText([('class:ansigray', f"  {html.escape(line)}")]))
