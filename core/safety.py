import re
from prompt_toolkit import prompt


# Patterns for dangerous commands that get an extra warning
DANGEROUS_PATTERNS = [
    (r"\brm\s+(-\w*r\w*f|--force|-\w*f\w*r)", "⚠ Recursive force delete"),
    (r"\brm\s+-rf\s+/(?:\s|$)", "🚨 DELETING ROOT FILESYSTEM"),
    (r"\bdd\s+", "⚠ Raw disk write"),
    (r"\bmkfs\b", "⚠ Filesystem format"),
    (r"\bchmod\s+-R\s+777", "⚠ Wide-open permissions recursively"),
    (r"\b>\s*/etc/", "⚠ Overwriting system config"),
    (r"\b>\s*/dev/", "⚠ Writing to device file"),
    (r":(){ :|:& };:", "🚨 Fork bomb detected"),
    (r"\bsudo\s+rm\b", "⚠ Root-level deletion"),
    (r"\bsudo\s+dd\b", "⚠ Root-level disk write"),
]


def detect_danger(command: str) -> list[str]:
    """Check a command for dangerous patterns. Returns list of warning messages."""
    warnings = []
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            warnings.append(message)
    return warnings


def confirm_tasks(commands: list[str]) -> str | None:
    """
    Show a planned execution sequence and ask for confirmation.
    Returns "all", "step", or None.
    """
    if not commands:
        return None

    print()
    print(f"\033[1;33m🤖 AI Tasks:\033[0m")
    
    for i, cmd in enumerate(commands, 1):
        warnings = detect_danger(cmd)
        warn_str = f" \033[1;91m[{'  '.join(warnings)}]\033[0m" if warnings else ""
        print(f"  \033[90m{i}.\033[0m \033[1;37m{cmd}\033[0m{warn_str}")

    print(f"\n\033[90m   [a] Run all   [s] Step-by-step   [n] Cancel\033[0m")

    while True:
        try:
            choice = prompt("   → ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return None

        if choice in ("a", "all", ""):
            return "all"
        elif choice in ("s", "step"):
            return "step"
        elif choice in ("n", "no", "cancel"):
            print("\033[90m   Cancelled.\033[0m")
            return None
        else:
            print("\033[90m   Type a, s, or n\033[0m")


def confirm_command(command: str) -> str | None:
    """
    Show the AI-generated command and ask for confirmation.

    Returns:
        - The command to execute (original or edited)
        - None if the user cancels
    """
    # Check for danger
    warnings = detect_danger(command)

    # Display the suggestion
    print()
    if warnings:
        print(f"\033[1;91m{'  '.join(warnings)}\033[0m")
    print(f"\033[1;33m🤖 AI suggests:\033[0m \033[1;37m{command}\033[0m")
    print(f"\033[90m   [y] Run  [n] Cancel  [e] Edit\033[0m")

    while True:
        try:
            choice = prompt("   → ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return None

        if choice in ("y", "yes", ""):
            return command

        elif choice in ("n", "no"):
            print("\033[90m   Cancelled.\033[0m")
            return None

        elif choice in ("e", "edit"):
            try:
                edited = prompt("   edit> ", default=command).strip()
                if edited:
                    # Re-check for danger after edit
                    new_warnings = detect_danger(edited)
                    if new_warnings:
                        print(f"\033[1;91m   {'  '.join(new_warnings)}\033[0m")
                    print(f"\033[1;33m   Run:\033[0m \033[1;37m{edited}\033[0m")
                    confirm = prompt("   Run? (y/n) → ").strip().lower()
                    if confirm in ("y", "yes", ""):
                        return edited
                    else:
                        print("\033[90m   Cancelled.\033[0m")
                        return None
                else:
                    print("\033[90m   Empty command, cancelled.\033[0m")
                    return None
            except (KeyboardInterrupt, EOFError):
                return None

        else:
            print("\033[90m   Type y, n, or e\033[0m")
