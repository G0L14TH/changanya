# launcher script

# STarted by Tauri as a subprocess
# run manually for testing: python ipc.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.shuffle_engine.ipc import run_ipc

run_ipc()


# if the album is played front to back and complete the engine 
# should play recommended tracks of the same artist or similar artists