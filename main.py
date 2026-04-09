import sys
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import ANSI
from core.command_executor import CommandExecutor
from core.config import Config


BANNER = r"""
\033[1;36m
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝

        J A R V I S
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
    print("\033[90m     Type 'exit' to quit.\033[0m\n")

    while True:
        try:
            user_input = prompt("jarvis> ").strip()

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