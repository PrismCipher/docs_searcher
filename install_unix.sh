#!/bin/bash

echo "========================================================"
echo "      DOCS CLI - INSTALLER (Linux / macOS)"
echo "========================================================"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed."
    echo "Please install python3 first (e.g. 'sudo apt install python3' or 'brew install python')."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "[INFO] pip3 not found, trying to bootstrap..."
    python3 -m ensurepip --default-pip
fi

echo "[INFO] Installing Docs CLI..."

pip3 install --user .

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "[WARNING] It seems ~/.local/bin is not in your PATH."
    echo "To fix this, run the following command:"
    echo "  export PATH=\$PATH:\$HOME/.local/bin"
    echo "And add it to your ~/.bashrc or ~/.zshrc"
fi

echo ""
echo "========================================================"
echo "[SUCCESS] Installation complete!"
echo "Try running: docs python print"
echo "========================================================"