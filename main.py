import sys
import os
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI
from core.command_executor import CommandExecutor
from core.config import Config
from core.voice import record_to_text


BANNER = r"""
\033[1;36m
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝

        
\033[0m
\033[90m  AI-Powered Shell • v0.2 • Type naturally or use commands\033[0m
"""


def main():
    # Print banner
    print(BANNER.replace("\\033[", "\033["))

    # Validate config
    warnings = Config.validate()
    if warnings:
        print("\033[1;93m⚠ Configuration warnings:\033[0m")
        for warn in warnings:
            print(f"\033[93m  • {warn}\033[0m")
        print("\033[90m  Using fallback AI model where necessary.\033[0m\n")

    executor = CommandExecutor()

    print("\033[90m  💡 Tips: Type shell commands directly, or describe what you want in plain English.\033[0m")
    print("\033[90m     Press Ctrl+V to speak. Type 'exit' to quit.\033[0m\n")

    history_file = os.path.expanduser("~/.jarvis/history.txt")
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    session_history = FileHistory(history_file)

    kb = KeyBindings()

    @kb.add('c-v')
    def _(event):
        """Press Ctrl+V to record voice."""
        print("\n\033[96m🎤 Listening... (Speak now)\033[0m")
        text = record_to_text(timeout=5)
        if text:
            event.app.current_buffer.insert_text(text)
        else:
            print("\033[93m⚠ Voice input failed or aborted.\033[0m")
        # Force redraw to clean up any visual tears
        event.app.invalidate()

    while True:
        try:
            user_input = prompt(
                "jarvis> ",
                history=session_history,
                auto_suggest=AutoSuggestFromHistory(),
                key_bindings=kb
            ).strip()

            if not user_input:
                continue

            if user_input in ("exit", "quit"):
                print("\n\033[1;36m👋 JARVIS signing off.\033[0m")
                break

            executor.execute(user_input)

        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print("\n\033[1;36m👋 JARVIS signing off.\033[0m")
            break

    executor.close()


if __name__ == "__main__":
    main()