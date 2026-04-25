"""
Configuration Module for SmartInventory.
Handles loading environment variables, setting up API clients,
and configuring fallback mechanisms for language models.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from google import genai

# Ensure .env is loaded from the project root regardless of OS
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

def reload_config():
    """
    Reloads API keys from the environment variables and re-initializes
    the API clients for Groq and Gemini. Resets the cached model.
    """
    global GROQ_API_KEY, GROQ_CLIENT, GEMINI_API_KEY, GEMINI_CLIENT, _GEMINI_MODEL_CACHE
    load_dotenv(dotenv_path=str(_ENV_PATH), override=True)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    try:
        GROQ_CLIENT = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    except Exception as error:
        print(f"[WARN] Failed to initialize Groq client: {error}")
        GROQ_CLIENT = None

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    try:
        GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
    except Exception as error:
        print(f"[WARN] Failed to initialize Gemini client: {error}")
        GEMINI_CLIENT = None
        
    _GEMINI_MODEL_CACHE = None

reload_config()

STAGE_DELAY = 15   # Seconds between staged API calls
MAX_RETRIES = 4    # Groq retry attempts on 429 before switching to Gemini
RETRY_BASE  = 10   # Base sleep seconds on first Groq 429 hit

# Gemini model — resolved lazily on first fallback
_GEMINI_MODEL_CACHE: str | None = None

def _get_gemini_model() -> str:
    """Resolves and caches the best available Gemini flash model."""
    global _GEMINI_MODEL_CACHE
    if _GEMINI_MODEL_CACHE:
        return _GEMINI_MODEL_CACHE
    if not GEMINI_CLIENT:
        raise ValueError("[FATAL] Gemini fallback requested but GEMINI_API_KEY is not set.")
    try:
        model_ids = [m.name.replace("models/", "") for m in GEMINI_CLIENT.models.list()]
    except Exception as exc:
        raise RuntimeError(f"[FATAL] Could not list Gemini models: {exc}")
    for candidate in ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]:
        match = next((m for m in model_ids if candidate in m), None)
        if match:
            _GEMINI_MODEL_CACHE = match
            print(f"[FALLBACK] Gemini model selected: {match}")
            return _GEMINI_MODEL_CACHE
    flash = [m for m in model_ids if "flash" in m.lower()]
    if flash:
        _GEMINI_MODEL_CACHE = flash[0]
        print(f"[FALLBACK] Gemini model selected (last resort): {flash[0]}")
        return _GEMINI_MODEL_CACHE
    raise RuntimeError(f"[FATAL] No Gemini flash model available. Models seen: {model_ids}")
