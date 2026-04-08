from core.pty_handler import ZshPTY


class CommandExecutor:
    def __init__(self):
        self.pty = ZshPTY()

    def execute(self, command: str) -> str:
        """Execute a command in the persistent ZSH session."""
        return self.pty.run_command(command)

    def close(self):
        self.pty.close()