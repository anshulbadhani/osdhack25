# src/online_chat.py
import asyncio
import websockets
import json
from datetime import datetime, timedelta
from prompt_toolkit import print_formatted_text, HTML
import threading

class OnlineChatClient:
    def __init__(self, server_url, username):
        self.server_url = server_url
        self.username = username
        self.websocket = None
        self.connected = False
        self.online_users = []
        self.message_history = []
        self.typing_display_task = None
        self.currently_typing_users = {}
        self.typing_display_lock = threading.Lock()
        
    def is_connected(self): return self.connected and self.websocket is not None
    def get_online_users(self): return self.online_users.copy()
    
    async def connect(self):
        try:
            ws_url = self.server_url.replace("http://", "ws://") + "/ws"
            print_formatted_text(HTML(f"<ansicyan>Connecting to {ws_url}...</ansicyan>"))
            self.websocket = await asyncio.wait_for(websockets.connect(ws_url), timeout=5.0)
            self.connected = True
            await self.websocket.send(json.dumps({"type": "join", "username": self.username}))
            print_formatted_text(HTML(f"<ansigreen>Connected to chat server as '{self.username}'</ansigreen>"))
            if not self.typing_display_task or self.typing_display_task.done():
                self.typing_display_task = asyncio.create_task(self._cleanup_typing_display())
            return True
        except Exception as e:
            print_formatted_text(HTML(f"<ansired>Connection failed: {e}. Is the server running?</ansired>"))
            return False
    
    async def listen_for_messages(self):
        try:
            async for message in self.websocket:
                try: await self.handle_message(json.loads(message))
                except (json.JSONDecodeError, TypeError): pass
        except websockets.exceptions.ConnectionClosed:
            print_formatted_text(HTML("<ansiyellow>Connection to chat server lost.</ansiyellow>"))
            self.connected = False

    async def handle_message(self, data):
        msg_type = data.get("type")
        with self.typing_display_lock:
            self._clear_typing_line()
            if msg_type == "chat":
                username, msg = data.get("username", "???"), data.get("message", "")
                if username in self.currently_typing_users: del self.currently_typing_users[username]
                if username == "Flowey": print_formatted_text(HTML(f"<ansiyellow>🌻 Flowey:</ansiyellow> <ansibrightyellow>{msg}</ansibrightyellow>"))
                elif username == "System": print_formatted_text(HTML(f"<ansibrightblue>*** {msg} ***</ansibrightblue>"))
                elif username == self.username: print_formatted_text(HTML(f"<ansibrightgreen>You:</ansibrightgreen> {msg}"))
                else: print_formatted_text(HTML(f"<ansibrightcyan>{username}:</ansibrightcyan> {msg}"))
            elif msg_type in ["user_joined", "user_left"]:
                self.online_users = data.get("users", [])
                color = "ansigreen" if msg_type == "user_joined" else "ansiyellow"
                print_formatted_text(HTML(f"<{color}>*** {data.get('username')} {msg_type.split('_')[1]} ({len(self.online_users)} users online) ***</{color}>"))
                if msg_type == "user_left" and data.get('username') in self.currently_typing_users: del self.currently_typing_users[data.get('username')]
            elif msg_type == "user_list": self.online_users = data.get("users", []); print_formatted_text(HTML(f"<ansibrightwhite>Online ({len(self.online_users)}): {', '.join(self.online_users)}</ansibrightwhite>"))
            elif msg_type == "ping": await self.websocket.send(json.dumps({"type": "pong"}))
            elif msg_type == "typing_status":
                typing_users = data.get("typing_users", [])
                for user in typing_users:
                    if user != self.username: self.currently_typing_users[user] = datetime.now()
                for user in list(self.currently_typing_users.keys()):
                    if user not in typing_users: del self.currently_typing_users[user]
            elif msg_type == "error": print_formatted_text(HTML(f"<ansired>Server Error: {data.get('message')}</ansired>"))
            self._redraw_typing_line()

    async def send_message(self, message: str):
        if not (self.is_connected() and message.strip()): return
        await self.websocket.send(json.dumps({"type": "chat", "message": message}))
    
    async def call_flowey(self, message: str):
        if not self.is_connected(): return
        await self.websocket.send(json.dumps({"type": "flowey", "message": message}))

    async def disconnect(self):
        if self.websocket:
            try: await self.websocket.send(json.dumps({"type": "leave"}))
            finally: await self.websocket.close(); self.websocket = None; self.connected = False
        if self.typing_display_task: self.typing_display_task.cancel()

    async def _cleanup_typing_display(self):
        while True:
            await asyncio.sleep(1)
            with self.typing_display_lock:
                to_remove = [u for u, dt in self.currently_typing_users.items() if datetime.now() - dt > timedelta(seconds=5)]
                if to_remove:
                    self._clear_typing_line()
                    for user in to_remove: del self.currently_typing_users[user]
                    self._redraw_typing_line()

    def _clear_typing_line(self):
        if self.currently_typing_users: print("\033[F\033[K", end="", flush=True)

    def _redraw_typing_line(self):
        if self.currently_typing_users:
            names = ", ".join(self.currently_typing_users.keys())
            print_formatted_text(HTML(f"<ansiyellow>... {names} is typing ...</ansiyellow>"), end="\n", flush=True)
            print("\033[F", end="", flush=True)