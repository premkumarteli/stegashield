#!/usr/bin/env bash
# StegaShield - Unified Development Environment Launcher (Bash)
# Usage: ./scripts/dev.sh

set -e

echo "=========================================="
echo "  StegaShield Dev Launcher (Linux/macOS)  "
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

cleanup() {
    echo ""
    echo "Stopping StegaShield services..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    echo "Done."
}

trap cleanup EXIT INT TERM

echo "[1/2] Starting FastAPI Backend on http://localhost:8000..."
cd "${BACKEND_DIR}"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

echo "[2/2] Starting Next.js Frontend on http://localhost:3000..."
cd "${FRONTEND_DIR}"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "StegaShield is running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both processes."
echo ""

wait
