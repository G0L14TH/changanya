import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.shuffle_engine.cli import run_cli

run_cli()