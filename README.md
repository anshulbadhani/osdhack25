# RETRERALE - The Dynamic Retro Terminal Launcher

Welcome to **RETRERALE**, a dynamic, AI-powered retro game launcher with a classic terminal aesthetic. Built with Python, this launcher automatically detects your games and emulators, supports removable "cartridge" drives, and features an integrated AI assistant with the personality of Flowey from Undertale.

## Features

-   **Dynamic Game Scanning:** Automatically scans `Games` and removable USB drives for your game ROMs. No manual configuration needed!
-   **Intelligent Emulator Detection:** Automatically finds emulators, whether they are placed in the local `Emulators` folder (portable setup) or installed system-wide (on Linux/macOS).
-   **AI-Powered Assistant:** Chat with "Flowey" for gaming advice, tips, or just some witty banter, powered by the Google Gemini API.
-   **Classic Terminal UI:** A fully-featured, keyboard-driven interface with a retro look and feel, complete with sounds for a nostalgic experience.
-   **Cross-Platform:** Designed to be OS-independent, working on Windows, macOS, and Linux.
-   **Highly Configurable:** Easily add support for new emulators and game types by editing a single configuration file.

## Getting Started

### Prerequisites

-   Python 3.10 or newer.

### Installation

1.  **Clone the repository** (or download and extract the source code):
    ```bash
    git clone https://github.com/your-username/RETRERALE.git
    cd RETRERALE
    ```

2.  **Create and activate a virtual environment:**
    -   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    -   **macOS / Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python retro_launcher.py
    ```

## Folder Structure

To use RETRERALE, you need to place your files in the correct folders:

/RetroFlow-Launcher/
│
├── venv/                     # Your Python virtual environment
│
├── retro_launcher.py         # The main script to run and build
├── requirements.txt          # The list of libraries to install
│
├── src/                      # The source code package
│   ├── __init__.py
│   ├── ai_chat.py
│   ├── audio.py
│   ├── config.py             # <-- Contains the updated EMULATOR_PROFILES
│   ├── game_manager.py       # <-- Contains the new find_emulator_path logic
│   ├── launcher.py
│   ├── ui.py
│   └── utils.py
│
├── Games/                    # (External) Place your game ROMs here
├── Emulators/                # (External) Place portable emulators here in subfolders
└── Sounds/                   # (External) Place your sound files here```



### Final Distribution Structure (What you give to users)

After you run the PyInstaller command, you will assemble the final release folder like this. The `.exe` will correctly look for the `Games`, `Emulators`, `Sounds`, `config.json`, and `retroflow.log` files alongside itself in this folder.

## How to Use

Simply launch the application and use the text commands to navigate.

-   `list`: Shows all detected games from local and cartridge sources.
-   `play <number>`: Launches the game corresponding to the number in the list.
-g   -   `info <number>`: Displays detailed information about a specific game.
-   `ai <prompt>`: Ask Flowey a question. (Requires an API key).
-   `apikey`: Set up your free Google Gemini API key to enable the AI.
-   `help`: Displays the full list of available commands.
-   `exit`: Closes the application.

## Adding New Emulators

Adding a new emulator is easy:

1.  **Open `src/config.py`**.
2.  **Add a new entry** to the `EMULATOR_PROFILES` dictionary. You need to specify the game file extension and the emulator's command name.

    **Example:** To add support for Sega Dreamcast (`.chd` files) with the `flycast` emulator:
    ```python
    EMULATOR_PROFILES = {
        # ... other entries
        '.chd': {'command': 'flycast', 'system': 'Sega Dreamcast', 'args': []},
    }
    ```

3.  **Provide the emulator:**
    -   **Option A (Recommended):** Create a folder named `Emulators/flycast/` and put the `flycast` executable inside it.
    -   **Option B (Linux/macOS):** Install `flycast` system-wide using your package manager (e.g., `sudo apt install flycast`).

The launcher will automatically detect and use the new configuration on the next startup.

## Building from Source

You can build a single-file executable using PyInstaller.

1.  Make sure you have followed the installation steps and have activated your virtual environment.
2.  Run the build command:
    ```bash
    pyinstaller --name RETRERALE --onefile retro_launcher.py
    ```
3.  The final executable will be located in the newly created `dist/` folder.

## Credits

-   Developed by **#ifndef BROS**.
-   Built with Python and the excellent `prompt-toolkit` library.
-   AI functionality powered by Google Gemini.
-   Flowey character from the game *Undertale* by Toby Fox.

---
