import os

def extract_file_contexts(user_input: str, cwd: str) -> str:
    """
    Scan user input for words that match existing files in the current directory.
    If match is found, append their contents to the prompt for AI awareness.
    """
    words = user_input.split()
    file_contents = []

    for word in words:
        # Strip common trailing/leading punctuation
        clean_word = word.strip(";'\",.")
        full_path = os.path.join(cwd, clean_word)
        
        # Avoid processing directories implicitly, max size 100kb to prevent blowing context
        if os.path.isfile(full_path) and os.path.getsize(full_path) < 100000:
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    # Truncate to 500 lines to preserve token limits
                    content_lines = []
                    for _ in range(500):
                        line = f.readline()
                        if not line:
                            break
                        content_lines.append(line)
                        
                    content = "".join(content_lines)
                    file_contents.append(f"<file path=\"{clean_word}\">\n{content}\n</file>")
            except UnicodeDecodeError:
                # Likely a binary file
                continue
            except Exception:
                continue

    if not file_contents:
        return ""
        
    return "\n\n--- INJECTED FILE CONTEXTS ---\n" + "\n\n".join(file_contents)

