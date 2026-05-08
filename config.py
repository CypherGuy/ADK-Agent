from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set.")
    return value


REPOS_PATH = Path(_require("REPOS_PATH"))
DIGEST_PATH = Path(_require("DIGEST_PATH"))
GEMINI_API_KEY = _require("GEMINI_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
DIGEST_LOOKBACK_DAYS = int(os.getenv("DIGEST_LOOKBACK_DAYS", "7"))
