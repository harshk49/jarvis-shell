import re
from prompt_toolkit import prompt


# Patterns for dangerous commands that get an extra warning
WARNING_PATTERNS = [
    (r"\brm\s+(-\w*r\w*f|--force|-\w*f\w*r)", "⚠ Recursive force delete"),
    (r"\bmkfs\b", "⚠ Filesystem format check"),
    (r"\bchmod\s+-R\s+777", "⚠ Wide-open permissions recursively"),
    (r"\bsudo\b", "⚠ Root-execution invoked"),
]

# Patterns for actively blocked commands
BLOCKED_PATTERNS = [
    (r"\brm\s+-rf\s+/(?:\s|$)", "🚨 Root filesystem deletion attempted"),
    (r"\bdd\s+if=.*of=/dev/", "🚨 Raw device overwrite attempted"),
    (r":(){ :|:& };:", "🚨 Fork bomb detected"),
    (r"\b>\s*/etc/", "🚨 Attempting to overwrite protected system config"),
]



def detect_danger(command: str) -> tuple[list[str], list[str]]:
    """Check a command for dangerous patterns. Returns (warnings, blocks) messages."""
    warnings = []
    blocks = []
    for pattern, message in WARNING_PATTERNS:
        if re.search(pattern, command):
            warnings.append(message)
    for pattern, message in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            blocks.append(message)
    return warnings, blocks


def confirm_tasks(commands: list[str]) -> str | None:
    """
    Show a planned execution sequence and ask for confirmation.
    Returns "all", "step", or None.
    """
    if not commands:
        return None

    print()
    print(f"\033[1;33m🤖 AI Tasks:\033[0m")
    
    fatal_error = False
    for i, cmd in enumerate(commands, 1):
        warnings, blocks = detect_danger(cmd)
        err_str = ""
        if blocks:
            err_str += f" \033[1;91m[BLOCKED: {' '.join(blocks)}]\033[0m"
            fatal_error = True
        elif warnings:
            err_str += f" \033[1;93m[{'  '.join(warnings)}]\033[0m"
            
        print(f"  \033[90m{i}.\033[0m \033[1;37m{cmd}\033[0m{err_str}")

    if fatal_error:
        print(f"\n\033[1;91m🚨 Fatal Safety Violation: One or more commands contain strictly prohibited operations. Aborting.\033[0m")
        return None

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
    warnings, blocks = detect_danger(command)

    # Display the suggestion
    print()
    if blocks:
        print(f"\033[1;91m🚨 BLOCKED OPERATION: {'  '.join(blocks)}\033[0m")
        print(f"\033[90m   This operation violates strict runtime safety constraints and cannot be executed.\033[0m")
        return None
        
    if warnings:
        print(f"\033[1;93m{'  '.join(warnings)}\033[0m")
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
                    new_warnings, new_blocks = detect_danger(edited)
                    if new_blocks:
                        print(f"\033[1;91m   🚨 BLOCKED: {'  '.join(new_blocks)}\033[0m")
                        print("\033[90m   Cancelled due to safety violation.\033[0m")
                        return None
                    if new_warnings:
                        print(f"\033[1;93m   {'  '.join(new_warnings)}\033[0m")
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
