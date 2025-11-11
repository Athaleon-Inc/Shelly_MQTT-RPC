#!/bin/bash
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "Starting Shelly MQTT-RPC Manager..."
python main.py
deactivate

