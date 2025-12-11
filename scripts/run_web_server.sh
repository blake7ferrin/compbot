#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5050}"

echo "[run_web_server] Project directory: ${ROOT_DIR}"
echo "[run_web_server] Using virtual environment: ${VENV_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[run_web_server] Creating virtual environment..."
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "[run_web_server] Installing Python dependencies..."
pip install --upgrade pip >/dev/null
pip install -r "${ROOT_DIR}/requirements.txt" >/dev/null

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  echo "[run_web_server] ERROR: Missing .env file. Copy .env.example and add your API keys."
  exit 1
fi

export FLASK_ENV="${FLASK_ENV:-production}"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

echo "[run_web_server] Starting Flask server on ${HOST}:${PORT}"
echo "[run_web_server] Press Ctrl+C to stop."
exec python "${ROOT_DIR}/app.py" --host "${HOST}" --port "${PORT}"
