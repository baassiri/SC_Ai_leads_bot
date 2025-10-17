#!/bin/bash

echo "============================================================"
echo "SC AI Lead Generation System - Starting Server"
echo "============================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "ERROR: Virtual environment not found"
    echo "Please run ./SETUP_MAC.sh first"
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""
echo "Starting Flask server..."
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""
echo "============================================================"

python backend/app.py
