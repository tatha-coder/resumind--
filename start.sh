#!/bin/bash
set -e

echo "========================================================"
echo "       RESUMIND AI - RESUME ANALYSIS STUDIO"
echo "========================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed or not in PATH."
    echo "Please install Python 3.10+."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment (venv)..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "[INFO] Installing / verifying dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================================"
echo " Launching Resumind AI at http://localhost:8501"
echo "========================================================"
echo ""
streamlit run app.py
