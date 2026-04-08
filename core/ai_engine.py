import re
import os
import platform
from google import genai
from core.config import Config


# System prompt that turns the LLM into a command generator
SYSTEM_PROMPT = """You are JARVIS, an intelligent shell command generator for Linux/ZSH.

Your ONLY job is to convert natural language into executable shell commands.

RULES:
1. Output ONLY the shell command. No explanations, no markdown, no backticks, no comments.
2. Prefer SAFE flags whenever possible:
   - Use `rm -i` instead of `rm` for deletions
   - Use `--dry-run` when available and the user didn't say "force" or "now"
   - Use `-i` (interactive) flags when destructive
3. NEVER generate commands that:
   - Wipe entire disks or partitions (dd if=/dev/zero, mkfs on system drives)
   - Delete root filesystem (rm -rf /)
   - Modify system-critical files (/etc/passwd, /etc/shadow) unless explicitly asked
   - Fork bombs or infinite loops
4. If the request is ambiguous, generate the SAFEST reasonable interpretation.
5. Combine commands logically when needed (using && or pipes).
6. Use modern tools when available (e.g., `rg` over `grep` if context suggests it).
7. Output exactly ONE command (can use pipes, &&, etc. but one logical command).

CONTEXT:
- Operating System: {os_info}
- Shell: ZSH
- Current Directory: {cwd}
"""


def _build_system_prompt(cwd: str) -> str:
    """Build the system prompt with current context."""
    os_info = f"{platform.system()} {platform.release()}"
    return SYSTEM_PROMPT.format(os_info=os_info, cwd=cwd)


def _clean_response(text: str) -> str:
    """Strip markdown code fences, backticks, and whitespace from AI response."""
    text = text.strip()
    # Remove ```bash ... ``` or ```sh ... ``` wrappers
    text = re.sub(r"^```(?:bash|sh|zsh|shell)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    # Remove inline backticks
    text = text.strip("`").strip()
    # Take only the first line if multiple were returned
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[0] if lines else text


class AIEngine:
    """Gemini-powered natural language to shell command translator."""

    def __init__(self):
        if not Config.AI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not configured.\n"
                "Get a free key at: https://aistudio.google.com/apikey\n"
                "Then add to .env: GEMINI_API_KEY=your_key_here"
            )

        self.client = genai.Client(api_key=Config.AI_API_KEY)
        self.model = Config.AI_MODEL

    def generate_command(self, user_input: str, cwd: str, retries: int = 2) -> str | None:
        """
        Convert natural language to a shell command.

        Args:
            user_input: The natural language request
            cwd: Current working directory for context
            retries: Number of retry attempts on failure

        Returns:
            Generated shell command string, or None on failure
        """
        system_prompt = _build_system_prompt(cwd)

        for attempt in range(retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_input,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.1,   # Low temp for precise commands
                        max_output_tokens=256,
                    ),
                )

                if response.text:
                    command = _clean_response(response.text)
                    if command:
                        return command

            except Exception as e:
                if attempt < retries:
                    continue
                print(f"\033[91m✗ AI Error: {e}\033[0m")
                return None

        return None
