#!/usr/bin/env bash
# AegisFlow One-Click Mission Control Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================================"
echo "🏥 AegisFlow — Regional Healthcare Lifeline Operations Portal"
echo "   Launching Institutional Light-Mode Web Interface at http://localhost:8501"
echo "================================================================================"

if [ -f "./.venv/bin/streamlit" ]; then
    ./.venv/bin/streamlit run app.py --server.headless=false
else
    streamlit run app.py --server.headless=false
fi
