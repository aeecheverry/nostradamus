#!/bin/bash

VENV_NAME="env_nostradamus"
PROJECT_DIR="."
cd "$PROJECT_DIR" || exit
if [ ! -d "$VENV_NAME" ]; then
    python -m venv "$VENV_NAME"
fi
source "$VENV_NAME/bin/activate"
pip install -r requirements.txt
