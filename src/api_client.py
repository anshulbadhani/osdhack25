# src/api_client.py

"""
This module contains the API client for interacting with the RetroFlow server,
handling online game catalog operations like fetching, searching, and downloading.
"""

import requests
import json
from pathlib import Path
from prompt_toolkit import print_formatted_text, HTML

from src.config import SERVER_URL
from src.utils import setup_and_log
from src.config import LOG_FILE, CONFIG_FILE

def log(level: str, message: str):
    """A local helper to call the main logging function with file paths."""
    setup_and_log(level, message, LOG_FILE, CONFIG_FILE)

class ApiClient:
    """A client to communicate with the RetroFlow server's REST API."""
    def __init__(self, games_directory: Path):
        self.api_base_url = SERVER_URL
        self.games_directory = games_directory
        self.headers = {'User-Agent': 'RetroFlowClient/1.0'}
        log("INFO", f"API Client initialized for server URL: {self.api_base_url}")

    def _check_server_health(self) -> bool:
        """Checks if the server is responsive."""
        try:
            health_url = f"{self.api_base_url}/health"
            response = requests.get(health_url, timeout=3, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            print_formatted_text(HTML(f"<ansired>Cannot connect to server at '{self.api_base_url}'. Is it running?</ansired>"))
            log("ERROR", f"Server health check failed for URL: {self.api_base_url}")
            return False

    def get_games(self) -> list | None:
        """Fetches the full list of games from the online catalog."""
        if not self._check_server_health(): return None
        try:
            response = requests.get(f"{self.api_base_url}/games", timeout=10, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print_formatted_text(HTML(f"<ansired>Error fetching games: {e}</ansired>"))
            log("ERROR", f"API request to /games failed: {e}")
            return None

    def search_games(self, query: str) -> list | None:
        """Searches the online catalog for games matching the query."""
        if not self._check_server_health(): return None
        try:
            params = {'q': query}
            response = requests.get(f"{self.api_base_url}/games/search", params=params, timeout=10, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print_formatted_text(HTML(f"<ansired>Search error: {e}</ansired>"))
            log("ERROR", f"API request to /games/search failed: {e}")
            return None

    def download_game(self, game_id: int) -> bool:
        """Downloads a game by its ID and saves it to the local games directory."""
        if not self._check_server_health(): return False
        try:
            info_response = requests.get(f"{self.api_base_url}/games/{game_id}", timeout=10, headers=self.headers)
            info_response.raise_for_status()
            game_info = info_response.json()
            filename = game_info.get('filename', f"game_{game_id}.rom")

            download_url = f"{self.api_base_url}/download/{game_id}"
            print_formatted_text(HTML(f"<ansicyan>Downloading '{game_info['name']}'...</ansicyan>"))
            log("INFO", f"Starting download for game ID {game_id} ({filename})")

            with requests.post(download_url, timeout=300, stream=True, headers=self.headers) as r:
                r.raise_for_status()
                file_path = self.games_directory / filename
                self.games_directory.mkdir(parents=True, exist_ok=True)
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r  Progress: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
            print() # Newline after progress bar
            print_formatted_text(HTML(f"<ansigreen>Successfully downloaded '{game_info['name']}' to {file_path}</ansigreen>"))
            log("INFO", f"Download complete for game ID {game_id}")
            return True
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print_formatted_text(HTML(f"<ansired>Download failed: {e}</ansired>"))
            log("ERROR", f"Download failed for game ID {game_id}: {e}")
            return False

    def request_server_scan(self) -> dict | None:
        """Asks the server to scan its incoming games folder."""
        if not self._check_server_health(): return None
        try:
            print_formatted_text(HTML("<ansicyan>Requesting server to scan for new games...</ansicyan>"))
            response = requests.post(f"{self.api_base_url}/admin/scan-games", timeout=120)
            response.raise_for_status()
            result = response.json()
            log("INFO", f"Server game scan requested. Result: {result}")
            return result
        except requests.exceptions.RequestException as e:
            print_formatted_text(HTML(f"<ansired>Error requesting game scan: {e}</ansired>"))
            log("ERROR", f"API request to /admin/scan-games failed: {e}")
            return None