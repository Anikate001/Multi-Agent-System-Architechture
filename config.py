"""
Configuration module for the Multi-Agent System.
Handles environment loading, LLM initialization, and system settings.
"""

import os
import sys
from dotenv import load_dotenv

# ── Load environment variables ──────────────────────────────────────────
load_dotenv()

# ── API Keys ────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ── Model Settings ──────────────────────────────────────────────────────
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))

# ── System Settings ─────────────────────────────────────────────────────
MAX_REVISIONS = 2          # Maximum feedback-loop retries
MAX_SEARCH_RESULTS = 5     # Tavily search result count
VERBOSE = True             # Print agent activity to console


def validate_config() -> bool:
    """Validate that required configuration is present."""
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your"):
        print("\n❌ ERROR: OPENAI_API_KEY is not set!")
        print("   1. Copy .env.example to .env")
        print("   2. Add your OpenAI API key")
        print("   → Get a key at: https://platform.openai.com/api-keys\n")
        return False
    return True


def get_llm():
    """
    Initialize and return the ChatOpenAI LLM instance.
    Uses langchain-openai (the current recommended package).
    """
    from langchain_openai import ChatOpenAI

    if not validate_config():
        sys.exit(1)

    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        api_key=OPENAI_API_KEY,
    )
