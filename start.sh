#!/usr/bin/env bash
# Start AgroSmart AI local development server
cd "$(dirname "$0")"
source .venv/bin/activate

if ! python -c "import sklearn" 2>/dev/null; then
  echo "Installing local dependencies (ML + export)..."
  pip install -r requirements.txt
fi

echo ""
echo "  AgroSmart AI is starting..."
echo "  Open: http://127.0.0.1:5000"
echo "  Press Ctrl+C to stop"
echo ""
python app.py
