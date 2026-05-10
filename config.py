from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env", override=True)


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set.")
    return value


REPOS_PATH = Path(_require("REPOS_PATH"))
DIGEST_PATH = Path(_require("DIGEST_PATH"))
GEMINI_API_KEY = _require("GEMINI_API_KEY")
DIGEST_LOOKBACK_DAYS = int(os.getenv("DIGEST_LOOKBACK_DAYS", "7"))
EXCLUDED_REPOS = [r.strip() for r in os.getenv(
    "EXCLUDED_REPOS", "").split(",") if r.strip()]
REPO_STALENESS_DAYS = int(os.getenv("REPO_STALENESS_DAYS", "180"))
DEFAULT_QUERY = os.getenv("DEFAULT_QUERY", "What should I build next?")
