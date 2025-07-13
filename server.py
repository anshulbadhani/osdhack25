# server.py
import shutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import uvicorn
from typing import List, Dict
import os
import logging
import google.generativeai as genai
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Directory Structure ---
SERVER_ROOT = Path(__file__).parent
DATABASE_PATH = SERVER_ROOT / "database.db"
GAMES_PUBLIC_PATH = SERVER_ROOT / "Games" / "Online" # Place downloaded games in a subfolder
GAMES_INCOMING_PATH = SERVER_ROOT / "IncomingGames" # Where admins place new ROMs to be scanned
GAMES_INCOMING_PATH.mkdir(parents=True, exist_ok=True)
GAMES_PUBLIC_PATH.mkdir(parents=True, exist_ok=True)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.users: Dict[str, dict] = {}
        self.ping_interval = 15
        self.ping_timeout = 5
        self.ping_tasks: Dict[str, asyncio.Task] = {}
        self.typing_users: Dict[str, datetime] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, username: str):
        async with self.lock:
            self.active_connections[username] = websocket
            self.users[username] = {
                "username": username,
                "connected_at": datetime.now().isoformat(),
                "last_pong": datetime.now()
            }
        self.ping_tasks[username] = asyncio.create_task(self.periodic_ping(username))
        await self.broadcast_user_event("user_joined", username)
    
    async def disconnect(self, username: str):
        async with self.lock:
            if username in self.active_connections: del self.active_connections[username]
            if username in self.users: del self.users[username]
            if username in self.ping_tasks: self.ping_tasks[username].cancel(); del self.ping_tasks[username]
            if username in self.typing_users: del self.typing_users[username]
    
    async def send_personal_message(self, message: str, username: str):
        async with self.lock:
            connection = self.active_connections.get(username)
        if connection:
            try:
                await connection.send_text(message)
            except Exception: await self.remove_connection(username)
    
    async def broadcast(self, message: str, exclude_user: str = None):
        async with self.lock:
            connections_to_broadcast = list(self.active_connections.items())
        for username, connection in connections_to_broadcast:
            if username != exclude_user:
                try:
                    await connection.send_text(message)
                except Exception: await self.remove_connection(username)
    
    async def broadcast_user_event(self, event_type: str, username: str):
        message = {"type": event_type, "username": username, "timestamp": datetime.now().isoformat(), "users": self.get_user_list()}
        await self.broadcast(json.dumps(message))

    async def broadcast_typing_status(self):
        async with self.lock:
            typing_usernames = list(self.typing_users.keys())
        message = {"type": "typing_status", "typing_users": typing_usernames, "timestamp": datetime.now().isoformat()}
        await self.broadcast(json.dumps(message))
    
    async def update_typing_status(self, username: str, is_typing: bool):
        changed = False
        async with self.lock:
            if is_typing:
                if username not in self.typing_users: changed = True
                self.typing_users[username] = datetime.now()
            elif username in self.typing_users:
                del self.typing_users[username]
                changed = True
        if changed: await self.broadcast_typing_status()
    
    async def remove_connection(self, username: str):
        await self.disconnect(username)
        await self.broadcast_user_event("user_left", username)
        await self.broadcast_typing_status()
    
    def get_user_list(self):
        return list(self.users.keys())

    async def periodic_ping(self, username: str):
        while True:
            await asyncio.sleep(self.ping_interval)
            async with self.lock:
                user_data = self.users.get(username); connection = self.active_connections.get(username)
            if not user_data or not connection: break
            try:
                await connection.send_text(json.dumps({"type": "ping"}))
                await asyncio.sleep(self.ping_timeout)
                async with self.lock: user_data_after_sleep = self.users.get(username)
                if user_data_after_sleep and (datetime.now() - user_data_after_sleep["last_pong"]) > timedelta(seconds=self.ping_timeout):
                    await self.remove_connection(username); break
            except asyncio.CancelledError: break
            except Exception: await self.remove_connection(username); break

manager = ConnectionManager()
SUPPORTED_EXTENSIONS = {
    '.nes': 'Nintendo Entertainment System', '.smc': 'Super Nintendo', '.sfc': 'Super Nintendo',
    '.gb': 'Game Boy', '.gbc': 'Game Boy Color', '.gba': 'Game Boy Advance',
    '.md': 'Sega Genesis', '.gen': 'Sega Genesis', '.n64': 'Nintendo 64',
    '.z64': 'Nintendo 64', '.ps1': 'PlayStation', '.bin': 'PlayStation', '.nds': 'Nintendo DS',
}

def init_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, filename TEXT UNIQUE NOT NULL,
            system TEXT NOT NULL, size INTEGER NOT NULL, description TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit(); conn.close()

def init_flowey():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: logger.warning("GEMINI_API_KEY environment variable not set. Flowey AI will be disabled."); return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        logger.error(f"Failed to initialize Flowey AI: {e}"); return None

flowey_model = init_flowey()
FLOWEY_SYSTEM_INSTRUCTION = ("You are Flowey the Flower from Undertale, now serving as a retro gaming assistant in an online chat...")

def format_size(b):
    if b < 1024: return f"{b} B"
    elif b < 1024**2: return f"{b/1024:.1f} KB"
    else: return f"{b/1024**2:.1f} MB"

async def get_flowey_response(message: str, username: str) -> str:
    if not flowey_model: return "Howdy! My AI brain isn't working right now."
    try:
        prompt = f"User {username} says: {message}"
        response = await flowey_model.generate_content_async(f"{FLOWEY_SYSTEM_INSTRUCTION}\n\n{prompt}")
        return response.text
    except Exception as e:
        logger.error(f"Error getting Flowey response: {e}"); return "*wilts slightly* I'm having trouble thinking..."

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    logger.info("RetroFlow Server started!"); yield
    logger.info("RetroFlow Server shutting down.")

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def scan_and_add_games():
    logger.info(f"Starting game scan in: {GAMES_INCOMING_PATH}")
    added_games, skipped_games = [], []
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    for file_path in GAMES_INCOMING_PATH.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                cursor.execute("SELECT id FROM games WHERE filename = ?", (file_path.name,))
                if cursor.fetchone(): skipped_games.append(f"{file_path.name} (exists)"); continue
                game_system = SUPPORTED_EXTENSIONS[file_path.suffix.lower()]
                cursor.execute('INSERT INTO games (name, filename, system, size, description) VALUES (?, ?, ?, ?, ?)',
                               (file_path.stem, file_path.name, game_system, file_path.stat().st_size, f"A classic {game_system} game."))
                destination_path = GAMES_PUBLIC_PATH / file_path.name
                shutil.move(str(file_path), str(destination_path))
                added_games.append(f"{file_path.stem} ({game_system})")
            except Exception as e: skipped_games.append(f"{file_path.name} (error: {e})")
    conn.commit(); conn.close()
    return {"added": added_games, "skipped": skipped_games, "added_count": len(added_games)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    username = None
    try:
        await websocket.accept()
        data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        message = json.loads(data)
        if message.get("type") == "join":
            username = message.get("username", f"User_{len(manager.users)+1}")
            async with manager.lock:
                if username in manager.active_connections:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Username taken."})); await websocket.close(); return
            await manager.connect(websocket, username)
            await websocket.send_text(json.dumps({"type": "chat", "username": "System", "message": f"Welcome, {username}!", "timestamp": datetime.now().isoformat()}))
            await websocket.send_text(json.dumps({"type": "user_list", "users": manager.get_user_list()}))
        else: await websocket.close(); return
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            if msg_type == "chat": await manager.broadcast(data, exclude_user=username); await manager.update_typing_status(username, False)
            elif msg_type == "flowey":
                flowey_response = await get_flowey_response(message.get("message", ""), username)
                flowey_message = {"type": "chat", "username": "Flowey", "message": flowey_response, "timestamp": datetime.now().isoformat()}
                await manager.broadcast(json.dumps(flowey_message)); await manager.update_typing_status(username, False)
            elif msg_type == "typing": await manager.update_typing_status(username, True)
            elif msg_type == "pong":
                async with manager.lock:
                    if username in manager.users: manager.users[username]["last_pong"] = datetime.now()
            elif msg_type == "leave": break
    except (WebSocketDisconnect, asyncio.TimeoutError, json.JSONDecodeError): pass
    finally:
        if username: await manager.remove_connection(username)

@app.get("/health")
async def health_check(): return {"status": "ok"}

@app.get("/games")
async def get_games_api():
    conn = sqlite3.connect(DATABASE_PATH); cursor = conn.cursor()
    cursor.execute('SELECT id, name, filename, system, size, description FROM games ORDER BY system, name')
    games = [{"id": r[0], "name": r[1], "filename": r[2], "system": r[3], "size": format_size(r[4]), "description": r[5]} for r in cursor.fetchall()]
    conn.close(); return games

@app.get("/games/search")
async def search_games_api(q: str):
    conn = sqlite3.connect(DATABASE_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id, name, filename, system, size, description FROM games WHERE name LIKE ? OR system LIKE ?", (f"%{q}%", f"%{q}%"))
    games = [{"id": r[0], "name": r[1], "filename": r[2], "system": r[3], "size": format_size(r[4]), "description": r[5]} for r in cursor.fetchall()]
    conn.close(); return games

@app.get("/games/{game_id}")
async def get_game_info_api(game_id: int):
    conn = sqlite3.connect(DATABASE_PATH); cursor = conn.cursor()
    cursor.execute('SELECT filename, name FROM games WHERE id = ?', (game_id,))
    row = cursor.fetchone(); conn.close()
    if not row: raise HTTPException(status_code=404, detail="Game not found")
    return {"filename": row[0], "name": row[1]}
    
@app.post("/download/{game_id}")
async def download_game_api(game_id: int):
    conn = sqlite3.connect(DATABASE_PATH); cursor = conn.cursor()
    cursor.execute('SELECT filename FROM games WHERE id = ?', (game_id,))
    row = cursor.fetchone(); conn.close()
    if not row: raise HTTPException(status_code=404, detail="Game not found")
    file_path = GAMES_PUBLIC_PATH / row[0]
    if not file_path.exists(): raise HTTPException(status_code=404, detail="Game file not found on server")
    return FileResponse(path=file_path, filename=row[0], media_type='application/octet-stream')

@app.post("/admin/scan-games")
async def trigger_game_scan_api():
    try: return JSONResponse(content=scan_and_add_games(), status_code=200)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("="*50)
    print("To add new games to the online catalog:")
    print(f"1. Place ROM files into the '{GAMES_INCOMING_PATH.resolve()}' directory.")
    print("2. Use the 'server scan' command in the RetroFlow client.")
    print("="*50)
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)