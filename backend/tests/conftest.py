"""Put backend/ on sys.path so tests import modules the same way the app does
(e.g. `from orchestration.graph import ...`)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
