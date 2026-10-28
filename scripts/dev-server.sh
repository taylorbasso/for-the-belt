#!/usr/bin/env bash
# Manage the local Flask dev server (127.0.0.1 only).
set -euo pipefail

cd "$(dirname "$0")/.."

# 5002: 5000 is taken by macOS AirPlay Receiver and 5001 by the biweekly-budget dev server.
PORT="${BELT_DEV_PORT:-5002}"
LOG_FILE=".dev-server.log"

find_pid() {
  # `|| true`: lsof exits non-zero when nothing matches, which would kill the script under pipefail.
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | awk '$1 ~ /^[Pp]ython/ {print $2; exit}' || true
}

start() {
  local pid
  pid="$(find_pid)"
  if [ -n "$pid" ]; then
    echo "Already running on http://127.0.0.1:$PORT (PID $pid)"
    return 0
  fi
  source .venv/bin/activate
  # ESPN_LEAGUE_ID, ESPN_S2, ESPN_SWID
  set -a; source .env; set +a
  nohup flask --app belt.app:create_app run --port "$PORT" > "$LOG_FILE" 2>&1 &
  disown
  sleep 3
  pid="$(find_pid)"
  if [ -z "$pid" ]; then
    echo "Failed to start — check $LOG_FILE" >&2
    exit 1
  fi
  echo "Started on http://127.0.0.1:$PORT (PID $pid)"
}

stop() {
  local pid
  pid="$(find_pid)"
  if [ -z "$pid" ]; then
    echo "Not running on port $PORT"
    return 0
  fi
  kill "$pid"
  sleep 1
  echo "Stopped (PID $pid)"
}

restart() {
  stop
  start
}

status() {
  local pid
  pid="$(find_pid)"
  if [ -n "$pid" ]; then
    echo "Running on http://127.0.0.1:$PORT (PID $pid)"
  else
    echo "Not running"
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}" >&2
    exit 1
    ;;
esac
