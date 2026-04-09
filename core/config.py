import os
from dotenv import load_dotenv

JARVISRC_PATH = os.path.expanduser("~/.jarvisrc")

if not os.path.exists(JARVISRC_PATH):
    default_config = """# JARVIS Global Configuration
GEMINI_API_KEY=""
JARVIS_AI_PROVIDER="gemini"
JARVIS_AI_MODEL="gemini-2.0-flash"

# Fallbacks
JARVIS_OLLAMA_URL="http://localhost:11434"
JARVIS_OLLAMA_MODEL="deepseek-coder"

# Sandbox / Safety
JARVIS_SANDBOX_MODE="False"
JARVIS_SAFETY_MODE="confirm"
"""
    try:
        with open(JARVISRC_PATH, "w") as f:
            f.write(default_config)
    except Exception:
        pass

load_dotenv(JARVISRC_PATH, override=True)


class Config:
    """Central configuration for JARVIS."""

    # Primary AI Provider (Gemini)
    AI_PROVIDER = os.getenv("JARVIS_AI_PROVIDER", "gemini")
    AI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL = os.getenv("JARVIS_AI_MODEL", "gemini-2.0-flash")

    # Fallback AI Provider (Ollama)
    OLLAMA_URL = os.getenv("JARVIS_OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", "deepseek-coder")

    # Safety config parameters
    SAFETY_MODE = os.getenv("JARVIS_SAFETY_MODE", "confirm")
    SANDBOX_MODE = os.getenv("JARVIS_SANDBOX_MODE", "False").lower() == "true"

    # Command timeout in seconds
    COMMAND_TIMEOUT = int(os.getenv("JARVIS_COMMAND_TIMEOUT", "30"))

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of config warnings, empty if fully configured."""
        warnings = []
        if not cls.AI_API_KEY:
            warnings.append(
                "GEMINI_API_KEY not set. Will fallback to Ollama (local)."
            )
        return warnings
