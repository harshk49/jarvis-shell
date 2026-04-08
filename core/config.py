import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


class Config:
    """Central configuration for JARVIS."""

    # AI Provider
    AI_PROVIDER = os.getenv("JARVIS_AI_PROVIDER", "gemini")
    AI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL = os.getenv("JARVIS_AI_MODEL", "gemini-2.0-flash")

    # Safety mode: "confirm" | "auto_safe" | "disabled"
    #   confirm    → always ask before running AI commands
    #   auto_safe  → auto-run safe commands, confirm dangerous ones
    #   disabled   → run everything without asking (not recommended)
    SAFETY_MODE = os.getenv("JARVIS_SAFETY_MODE", "confirm")

    # Command timeout in seconds
    COMMAND_TIMEOUT = int(os.getenv("JARVIS_COMMAND_TIMEOUT", "30"))

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of config errors, empty if valid."""
        errors = []
        if not cls.AI_API_KEY:
            errors.append(
                "GEMINI_API_KEY not set. Add it to .env or export it:\n"
                "  echo 'GEMINI_API_KEY=your_key_here' >> .env"
            )
        return errors
