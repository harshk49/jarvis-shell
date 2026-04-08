import subprocess
import os
import sys


class ZshPTY:
    """Executes commands in ZSH subprocesses with persistent state (cwd, env)."""

    def __init__(self):
        self.cwd = os.getcwd()
        self.env = os.environ.copy()

    def run_command(self, command: str) -> str:
        """Execute a command in ZSH and stream output live."""

        # Wrap the command to:
        #   1. Run the user's command
        #   2. Print the final working directory so we can track cd
        wrapper = f'{command}\n__EXIT_CODE=$?\necho ""\necho "__JARVIS_CWD__:$PWD"\nexit $__EXIT_CODE'

        try:
            result = subprocess.run(
                ["/bin/zsh", "-c", wrapper],
                cwd=self.cwd,
                env=self.env,
                capture_output=True,
                text=True,
                timeout=30,
            )

            stdout = result.stdout
            stderr = result.stderr

            # Extract and update cwd from output
            lines = stdout.splitlines()
            clean_lines = []
            for line in lines:
                if line.startswith("__JARVIS_CWD__:"):
                    new_cwd = line.split(":", 1)[1].strip()
                    if os.path.isdir(new_cwd):
                        self.cwd = new_cwd
                else:
                    clean_lines.append(line)

            output = "\n".join(clean_lines).rstrip()

            # Print stdout
            if output:
                print(output)

            # Print stderr
            if stderr.strip():
                print(f"\033[91m{stderr.strip()}\033[0m", file=sys.stderr)

            return output

        except subprocess.TimeoutExpired:
            print("\033[93m⚠ Command timed out after 30s\033[0m")
            return ""
        except Exception as e:
            print(f"\033[91m✗ Error: {e}\033[0m")
            return ""

    def close(self):
        """No persistent process to close."""
        pass