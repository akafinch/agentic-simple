"""Centralized configuration from environment variables."""

# ChromaDB (pulled in by CrewAI) requires sqlite3 >= 3.35.
# On some systems the bundled sqlite3 is too old; pysqlite3-binary ships a newer one.
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# VM Role
ROLE = os.getenv("ROLE", "orchestrator")

# Host IPs
ORCHESTRATOR_HOST = os.getenv("ORCHESTRATOR_HOST", "10.0.0.1")
SPECIALIST_HOST = os.getenv("SPECIALIST_HOST", "10.0.0.2")

# Model config
MANAGER_MODEL = os.getenv("MANAGER_MODEL", "ollama/gemma3:27b")
MANAGER_BASE_URL = os.getenv("MANAGER_BASE_URL", f"http://{ORCHESTRATOR_HOST}:11434")
SPECIALIST_MODEL = os.getenv("SPECIALIST_MODEL", "ollama/gemma3:12b")
SPECIALIST_BASE_URL = os.getenv("SPECIALIST_BASE_URL", f"http://{SPECIALIST_HOST}:11434")

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
CHARTS_DIR = BASE_DIR / os.getenv("CHARTS_DIR", "output/charts")

# Dev
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# Ensure output dirs exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
