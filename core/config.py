import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class Config:
    """Central configuration for JARVIS."""

    # Primary AI Provider (Gemini)
    AI_PROVIDER = os.getenv("JARVIS_AI_PROVIDER", "gemini")
    AI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL = os.getenv("JARVIS_AI_MODEL", "gemini-2.0-flash")

    # Fallback AI Provider (Ollama)
    OLLAMA_URL = os.getenv("JARVIS_OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", "deepseek-coder")

    # Safety mode: "confirm" | "auto_safe" | "disabled"
    SAFETY_MODE = os.getenv("JARVIS_SAFETY_MODE", "confirm")

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
