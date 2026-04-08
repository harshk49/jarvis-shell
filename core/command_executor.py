from core.pty_handler import ZshPTY
from core.ai_engine import AIEngine
from core.classifier import classify
from core.safety import confirm_command


class CommandExecutor:
    def __init__(self):
        self.pty = ZshPTY()
        self.ai = None  # Lazy-loaded on first NL input

    def _get_ai(self) -> AIEngine:
        """Lazy-init AI engine (only when needed)."""
        if self.ai is None:
            self.ai = AIEngine()
        return self.ai

    def execute(self, user_input: str) -> str:
        """
        Route user input: direct commands run immediately,
        natural language goes through AI → confirm → execute.
        """
        input_type = classify(user_input)

        if input_type == "command":
            return self.pty.run_command(user_input)

        # Natural language path
        return self._handle_natural_language(user_input)

    def _handle_natural_language(self, user_input: str) -> str:
        """AI pipeline: generate → confirm → execute."""
        try:
            ai = self._get_ai()
        except ValueError as e:
            print(f"\033[91m{e}\033[0m")
            return ""

        # Generate command from AI
        print(f"\033[90m🧠 Thinking...\033[0m", end="", flush=True)
        command = ai.generate_command(user_input, cwd=self.pty.cwd)
        # Clear the "Thinking..." line
        print("\r\033[K", end="")

        if not command:
            print("\033[91m✗ AI couldn't generate a command. Try rephrasing.\033[0m")
            return ""

        # Safety confirmation
        final_command = confirm_command(command)

        if final_command is None:
            return ""

        # Execute the approved command
        print()
        return self.pty.run_command(final_command)

    def close(self):
        self.pty.close()