from prompt_toolkit import prompt
from core.command_executor import CommandExecutor


def main():
    executor = CommandExecutor()

    print("\033[1;36m⚡ JARVIS Shell v0.1\033[0m")
    print("\033[90mType commands like a normal shell. 'exit' to quit.\033[0m\n")

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