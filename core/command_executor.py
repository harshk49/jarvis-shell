import time
import sys
from core.pty_handler import ZshPTY
from core.ai_engine import AIEngine
from core.classifier import classify
from core.config import Config
from core.safety import confirm_command, confirm_tasks
from core.memory import MemoryManager

def typewriter_print(text: str, speed: float = 0.015):
    """Subtly animate text outputs."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    print()



class CommandExecutor:
    def __init__(self):
        self.pty = ZshPTY()
        self.memory = MemoryManager()
        self.ai = None  # Lazy-loaded on first NL input

    def _get_ai(self) -> AIEngine:
        """Lazy-init AI engine (only when needed)."""
        if self.ai is None:
            self.ai = AIEngine(memory_manager=self.memory)
        return self.ai

    def execute(self, user_input: str) -> str:
        """
        Route user input: direct commands run immediately,
        natural language goes through AI → confirm → execute.
        """
        input_type = classify(user_input)

        if input_type == "command":
            if Config.SANDBOX_MODE:
                print(f"\033[93m[SANDBOX MODE] Simulated direct execution: {user_input}\033[0m")
                return ""
                
            output = self.pty.run_command(user_input)
            self.memory.record_command("direct_command", user_input, success=True)
            return output

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
        ai_output = ai.generate_command(user_input, cwd=self.pty.cwd)
        # Clear the "Thinking..." line
        print("\r\033[K", end="")

        if not ai_output or not isinstance(ai_output, dict):
            print("\033[91m✗ AI couldn't generate a valid sequence. Try rephrasing.\033[0m")
            return ""

        explanation = ai_output.get("explanation", "").strip()
        commands = ai_output.get("commands", [])

        if explanation:
            sys.stdout.write("\033[1;36m💬 Jarvis:\033[0m ")
            sys.stdout.flush()
            typewriter_print(f"\033[1;36m{explanation}\033[0m", speed=0.015)
            print()
            
        if not commands:
            # Maybe the user just asked for a summary and no commands were needed
            return ""

        # Single Command Flow
        if len(commands) == 1:
            final_command = confirm_command(commands[0])
            if not final_command:
                return ""
                
            print()
            self.memory.record_command(user_input, final_command, success=True)
            if Config.SANDBOX_MODE:
                print(f"\033[93m[SANDBOX MODE] Skipped execution of single string: {final_command}\033[0m")
                return ""
                
            return self.pty.run_command(final_command)

        # Multi-Step Task Flow
        mode = confirm_tasks(commands)
        if not mode:
            return ""
            
        output_accum = []
        for cmd in commands:
            if mode == "step":
                final_command = confirm_command(cmd)
                if not final_command:
                    print("\033[90m   Workflow aborted.\033[0m")
                    break
            else:
                final_command = cmd
                print(f"\n\033[90mExecuting:\033[0m \033[1;37m{final_command}\033[0m")
                
            self.memory.record_command(user_input, final_command, success=True)
            if Config.SANDBOX_MODE:
                print(f"  \033[93m[SANDBOX MODE] Simulated Output Skipped for: {final_command}\033[0m")
                continue
                
            out = self.pty.run_command(final_command)
            output_accum.append(out)
            
        return "\n".join(output_accum)

    def close(self):
        self.pty.close()