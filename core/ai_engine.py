import re
import os
import platform
import subprocess
import requests
from google import genai
from core.config import Config
from core.memory import MemoryManager


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
- Top 5 CPU Processes:
{active_processes}
- Recent Conversational Command History:
{recent_history}
- User Preferences/Aliases:
{preferences}
"""


def _get_active_processes() -> str:
    """Get basic overview of current user heavy processes."""
    try:
        user = os.environ.get("USER", "")
        # Get top 5 CPU processes for current user
        output = subprocess.check_output(
            ["ps", "-u", user, "-o", "pid,comm,%cpu", "--sort=-%cpu"],
            text=True, stderr=subprocess.DEVNULL
        )
        lines = output.strip().splitlines()
        # Return header + top 5
        return "\n".join(lines[:6])
    except Exception:
        return "Unavailable"


def _build_system_prompt(cwd: str, memory: MemoryManager = None) -> str:
    """Build the system prompt with current context."""
    os_info = f"{platform.system()} {platform.release()}"
    
    active_procs = _get_active_processes()
    history_text = "None"
    prefs_text = "None"
    
    if memory:
        recent = memory.get_recent_commands(limit=5)
        if recent:
            history_text = "\n".join([f"Q: {r['original_query']} -> A: {r['executed_command']}" for r in recent])
        
        prefs = memory.get_all_preferences()
        if prefs:
            prefs_text = "\n".join([f"{k}: {v}" for k, v in prefs.items()])

    return SYSTEM_PROMPT.format(
        os_info=os_info, 
        cwd=cwd, 
        active_processes=active_procs,
        recent_history=history_text,
        preferences=prefs_text
    )


def _clean_response(text: str) -> str:
    """Strip markdown code fences, backticks, and whitespace from AI response."""
    text = text.strip()
    
    # If the response contains markdown code blocks, extract the content of the first one
    block_match = re.search(r"```(?:bash|sh|zsh|shell)?\s*(.*?)```", text, re.DOTALL)
    if block_match:
        text = block_match.group(1).strip()
    else:
        # Otherwise, fall back to removing inline backticks and conversational filler
        text = text.strip("`").strip()
        # Remove typical conversational prefixes if no code block was used
        text = re.sub(r"^(?:Sure|Here|The command|To [a-z]+)[^\n]*:\s*\n?", "", text, flags=re.IGNORECASE).strip()

    # Take only the first line if multiple were returned (useful for 1-liner commands)
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[0] if lines else text


class AIEngine:
    """Natural language to shell command translator with Gemini + Ollama fallback."""

    def __init__(self, memory_manager: MemoryManager = None):
        self.memory = memory_manager
        self.gemini_client = None
        if Config.AI_API_KEY:
            self.gemini_client = genai.Client(api_key=Config.AI_API_KEY)
        self.gemini_model = Config.AI_MODEL
        self.ollama_url = Config.OLLAMA_URL
        self.ollama_model = Config.OLLAMA_MODEL

    def _generate_with_gemini(self, system_prompt: str, user_input: str) -> str | None:
        if not self.gemini_client:
            return None
        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=user_input,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,   # Low temp for precise commands
                    max_output_tokens=256,
                ),
            )
            if response.text:
                return _clean_response(response.text)
        except Exception as e:
            print(f"\r\033[K\033[93m⚠ Gemini API failed: {e}. Falling back to Ollama...\033[0m")
        return None

    def _generate_with_ollama(self, system_prompt: str, user_input: str) -> str | None:
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": user_input,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 256
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=Config.COMMAND_TIMEOUT)
            response.raise_for_status()
            text = response.json().get("response", "")
            return _clean_response(text) if text else None
        except requests.exceptions.RequestException as e:
            print(f"\r\033[K\033[91m✗ Ollama failed: {e}\033[0m")
            return None

    def generate_command(self, user_input: str, cwd: str, retries: int = 1) -> str | None:
        """
        Convert natural language to a shell command.
        """
        system_prompt = _build_system_prompt(cwd, self.memory)

        for _ in range(retries + 1):
            command = None
            
            # Try primary provider (Gemini) if configured
            if self.gemini_client:
                command = self._generate_with_gemini(system_prompt, user_input)
                
            # If primary fails or is not configured, fall back to Ollama
            if not command:
                command = self._generate_with_ollama(system_prompt, user_input)

            if command:
                return command

        return None
