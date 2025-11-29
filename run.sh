#!/bin/bash

# Smart Bulb Screen Sync - Linux Launch Script

SILENT=0
MINIMIZED=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --silent)
            SILENT=1
            ;;
        --minimized)
            MINIMIZED=1
            ;;
    esac
done

log() {
    if [ $SILENT -eq 0 ]; then
        echo "$1"
    fi
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

log "[1/4] Checking for Python installation..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    log "[ERROR] Python 3 is not installed!"
    log "Please install Python 3.11+ using your package manager:"
    log "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    log "  Fedora: sudo dnf install python3 python3-pip"
    log "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log "[OK] Found Python $PYTHON_VERSION"

# Check Python version (basic check)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    log "[WARNING] Python 3.11+ is recommended. You have Python $PYTHON_VERSION"
    log "Continuing anyway..."
fi

log ""
log "[2/4] Checking virtual environment..."

# Check if venv exists
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    log "[OK] Virtual environment found"
else
    log "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        log "[ERROR] Failed to create virtual environment!"
        exit 1
    fi
    log "[OK] Virtual environment created"
fi

log ""
log "[3/4] Installing dependencies..."

# Activate virtual environment
source venv/bin/activate

# Check if packages are installed
python3 -c "import customtkinter, kasa, mss, numpy, watchfiles" &> /dev/null

if [ $? -ne 0 ]; then
    if [ $SILENT -eq 0 ]; then
        log "[INFO] Installing packages from requirements.txt..."
        log "This may take a few minutes on first run..."
        log ""
        pip install -r requirements.txt
    else
        pip install -r requirements.txt &> /dev/null
    fi

    if [ $? -ne 0 ]; then
        log ""
        log "[ERROR] Failed to install requirements!"
        exit 1
    fi

    log ""
    log "[OK] All packages installed"
else
    log "[OK] All packages already installed"
fi

log ""
if [ $SILENT -eq 0 ]; then
    log "[4/4] Starting Smart Bulb Screen Sync..."
    log "================================================"
    log ""
    log "Program is starting in the background..."
    log "You can close this terminal - the program will keep running!"
    log "Look for the light bulb icon in your system tray."
    log ""
fi

# Build arguments for main.py
MAIN_ARGS=""
if [ $MINIMIZED -eq 1 ]; then
    MAIN_ARGS="--minimized"
fi

# Start the program in background
if [ $SILENT -eq 0 ]; then
    python3 main.py $MAIN_ARGS &
    log "[OK] Program launched successfully! (PID: $!)"
    log ""
    sleep 2
else
    nohup python3 main.py $MAIN_ARGS > /dev/null 2>&1 &
fi

deactivate