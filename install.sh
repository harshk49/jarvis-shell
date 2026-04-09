#!/bin/bash
set -e

echo "[*] Installing Jarvis..."
REPO_URL="https://github.com/harshk49/jarvis-shell.git"
INSTALL_DIR="$HOME/.jarvis-shell"
BIN_DIR="$HOME/.local/bin"

if ! command -v python3 &> /dev/null; then
    echo "[!] Error: python3 is required."
    exit 1
fi
if ! command -v git &> /dev/null; then
    echo "[!] Error: git is required."
    exit 1
fi

if [ -d "$INSTALL_DIR" ]; then
    echo "[*] Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main || true
else
    echo "[*] Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[*] Installing dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "[*] Creating CLI executable..."
mkdir -p "$BIN_DIR"
cat << 'EOF' > "$BIN_DIR/jarvis"
#!/bin/bash
"$HOME/.jarvis-shell/venv/bin/python" "$HOME/.jarvis-shell/main.py" "$@"
EOF

chmod +x "$BIN_DIR/jarvis"

echo ""
echo "=============================="
echo "[x] Installation Complete!"
echo "Make sure $BIN_DIR is in your PATH."
echo "Try running: jarvis"
echo "=============================="
