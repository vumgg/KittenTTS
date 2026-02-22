#!/bin/bash
# KittenTTS Web Interface Startup Script for Linux/macOS

echo "========================================"
echo "   KittenTTS Web Interface"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3 first"
    exit 1
fi

echo "Installing/updating dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo ""
echo "========================================"
echo "Starting KittenTTS Web Interface..."
echo "========================================"
echo ""
echo "Open your browser and go to:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python3 app.py
