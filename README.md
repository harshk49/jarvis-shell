# JARVIS (AI-Powered Shell) 🧠💻

Jarvis transforms your standard terminal environment into a highly intelligent, context-aware command executor capable of directly translating natural language into safe, runnable shell commands.

## Key Capabilities
- **Voice Control**: Hit `Ctrl+V` to inject spoken commands natively into your prompt. 
- **Context Injection**: Need to alter a file? Say `Modify src/index.js to implement auth`. Jarvis automatically retrieves `src/index.js` contents to generate pinpoint diff commands.
- **Workflow Automation**: Group highly complex sequence requests into automated, step-by-step terminal lists.
- **Root Level Safety Guardrails**: Prevents destructive actions explicitly while granting simulation through **Sandbox Mode**.

## Installation

Run the one-liner installer directly in your terminal:
```bash
curl -sL https://raw.githubusercontent.com/harshk49/jarvis-shell/main/install.sh | bash
```

*Note: Ensure your `~/.local/bin` folder is exposed in your system `$PATH`.*
If you wish to use the Voice features, verify you have OS-level Portaudio libraries installed (e.g., `sudo apt install portaudio19-dev`).

## Configuration
Upon first run, Jarvis generates a `~/.jarvisrc` dotfile configuring the default environment variables. Apply your Google GenAI Key there:
```text
GEMINI_API_KEY="AIzaSyYourKeyHere..."
JARVIS_SANDBOX_MODE="False"
```

## Quick Start
Run `jarvis` from anywhere in your directory tree. 

```bash
jarvis> summarize core/safety.py
jarvis> deploy an express boilerplate and install nodemon
```
