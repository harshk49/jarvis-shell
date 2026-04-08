import re
import shutil

# Common shell commands/binaries that indicate direct command input
DIRECT_COMMAND_PREFIXES = {
    # Navigation & files
    "ls", "cd", "pwd", "cp", "mv", "rm", "mkdir", "rmdir", "touch",
    "cat", "head", "tail", "less", "more", "wc", "file", "stat",
    "chmod", "chown", "chgrp", "ln",
    # Search & text
    "find", "grep", "egrep", "fgrep", "rg", "ag", "sed", "awk",
    "sort", "uniq", "cut", "tr", "diff", "comm", "xargs",
    # System
    "ps", "top", "htop", "kill", "killall", "df", "du", "free",
    "uname", "whoami", "id", "uptime", "hostname", "date", "cal",
    "mount", "umount", "lsblk", "fdisk",
    # Network
    "ping", "curl", "wget", "ssh", "scp", "rsync", "nc", "netstat",
    "ss", "ip", "ifconfig", "dig", "nslookup", "traceroute",
    # Package management
    "apt", "apt-get", "dpkg", "yum", "dnf", "pacman", "snap",
    "pip", "pip3", "npm", "npx", "yarn", "cargo", "go",
    # Dev tools
    "git", "docker", "docker-compose", "make", "cmake", "gcc", "g++",
    "python", "python3", "node", "java", "javac", "rustc",
    # Editors & misc
    "vim", "vi", "nano", "code", "emacs",
    "echo", "printf", "env", "export", "source", "alias", "which",
    "man", "help", "type", "history", "clear", "reset",
    "tar", "zip", "unzip", "gzip", "gunzip", "bzip2", "xz",
    "sudo", "su", "systemctl", "journalctl", "service",
}

# Patterns that strongly suggest direct shell commands
COMMAND_PATTERNS = [
    r"^\./",            # ./script.sh
    r"^/",              # /usr/bin/something
    r"^~",              # ~/script.sh
    r"\|",              # pipes
    r"[12]?>",          # redirects
    r"&&",              # chaining
    r"\|\|",            # or chaining
    r";\s*\w",          # semicolon chaining
    r"^\$\(",           # command substitution
    r"^!\w",            # history expansion
]

# Words that strongly suggest natural language
NL_INDICATORS = {
    "show", "display", "list", "find", "search", "delete", "remove",
    "create", "make", "open", "close", "start", "stop", "restart",
    "install", "uninstall", "update", "upgrade",
    "check", "tell", "what", "how", "where", "which", "who",
    "give", "get", "set", "change", "modify", "rename",
    "compress", "extract", "download", "upload",
    "clean", "clear", "free", "monitor", "watch",
    "all", "every", "the", "my", "this", "that", "those", "these",
    "please", "can", "could", "would", "should",
    "files", "folders", "directories", "processes", "services",
    "bigger", "smaller", "largest", "newest", "oldest",
    "running", "listening", "using", "taking",
}


def classify(user_input: str) -> str:
    """
    Classify user input as 'command' or 'natural_language'.

    Returns:
        'command'          — execute directly in shell
        'natural_language' — send to AI for translation
    """
    text = user_input.strip()

    if not text:
        return "command"

    # Check if the first word is a known command/binary
    first_word = text.split()[0].lower()

    # Strip leading sudo
    words = text.split()
    base_word = words[1].lower() if words[0] == "sudo" and len(words) > 1 else first_word

    # Direct command by known prefix
    if base_word in DIRECT_COMMAND_PREFIXES:
        return "command"

    # Check if the binary exists on PATH
    if shutil.which(base_word):
        return "command"

    # Check for shell command patterns (pipes, redirects, paths)
    for pattern in COMMAND_PATTERNS:
        if re.search(pattern, text):
            return "command"

    # Check for environment variable assignment: FOO=bar
    if re.match(r"^[A-Z_][A-Z0-9_]*=", text):
        return "command"

    # If input looks like natural language
    input_words = set(text.lower().split())
    nl_match_count = len(input_words & NL_INDICATORS)

    # Strong NL signal: multiple NL words or a question
    if nl_match_count >= 2:
        return "natural_language"

    # Single word that's an NL verb but not a binary
    if len(words) == 1 and first_word in NL_INDICATORS:
        return "natural_language"

    # Longer inputs with spaces that aren't recognized commands → likely NL
    if len(words) >= 3 and nl_match_count >= 1:
        return "natural_language"

    # If it has 4+ words and no command patterns matched → probably NL
    if len(words) >= 4:
        return "natural_language"

    # Default: treat as command (let the shell handle errors)
    return "command"
