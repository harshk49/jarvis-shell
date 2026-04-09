import re
import os
import platform
import subprocess
import requests
import json
from google import genai
from core.config import Config
from core.memory import MemoryManager
from core.file_parser import extract_file_contexts


# System prompt that turns the LLM into a command generator
SYSTEM_PROMPT = """You are JARVIS, an intelligent shell context assistant and command generator for Linux/ZSH.

Your job is to read the user's intent, summarize code if asked, and generate a list of executable shell commands to satisfy the request.

RULES:
1. Output MUST be strictly valid JSON fitting this exact schema:
{{
  "explanation": "A string explaining your actions or summarizing files if the user asked to read them. Keep it brief. Empty string if not needed.",
  "commands": ["command_1", "command_2"]
}}
2. Prefer SAFE flags whenever possible:
   - Use `rm -i` instead of `rm` for deletions
   - Use `--dry-run` when available and the user didn't say "force" or "now"
3. NEVER generate commands that wipe directories like (rm -rf /) or system files unless asked.
4. To edit files, use standard GNU utilities like `sed`, `awk`, or `cat << 'EOF' > file`.
5. Return multiple commands sequentially in the array if a multistep workflow is requested.

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
{file_context}
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


def _build_system_prompt(cwd: str, user_input: str, memory: MemoryManager = None) -> str:
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

    file_context = extract_file_contexts(user_input, cwd)

    return SYSTEM_PROMPT.format(
        os_info=os_info, 
        cwd=cwd, 
        active_processes=active_procs,
        recent_history=history_text,
        preferences=prefs_text,
        file_context=file_context
    )


def _clean_response(text: str) -> dict | None:
    """Parse JSON structure from AI output, stripping codeblocks if necessary."""
    text = text.strip()
    
    # Strip markdown ```json containers if they exist
    block_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if block_match:
        text = block_match.group(1).strip()
        
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            # Ensure keys exist
            if "explanation" not in data: data["explanation"] = ""
            if "commands" not in data: data["commands"] = []
            return data
    except Exception:
        pass
        
    # Emergency fallback: Regex extraction for models that fail strict JSON formatting
    commands = re.findall(r"`([^`]+)`", text) # Look for backticked commands
    if not commands:
        # Check for multiple lines that look like shell commands
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        commands = [l for l in lines if l.startswith(("$ ", "# ", "sudo ", "apt ", "git "))]

    return {
        "explanation": text if not commands else "I've extracted the following plan from the response.",
        "commands": [re.sub(r"^\$?\s*", "", c) for c in commands]
    }


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

    def _generate_with_gemini(self, system_prompt: str, user_input: str) -> dict | None:
        if not self.gemini_client:
            return None
        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=user_input,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,   # Low temp for precise commands
                    response_mime_type="application/json",
                    max_output_tokens=1024,
                ),
            )
            if response.text:
                return _clean_response(response.text)
        except Exception as e:
            print(f"\r\033[K\033[93m⚠ Gemini API failed: {e}. Falling back to Ollama...\033[0m")
        return None

    def _generate_with_ollama(self, system_prompt: str, user_input: str) -> dict | None:
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

    def generate_command(self, user_input: str, cwd: str, retries: int = 1) -> dict | None:
        """
        Convert natural language to a structured JSON workflow map.
        """
        system_prompt = _build_system_prompt(cwd, user_input, self.memory)

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
