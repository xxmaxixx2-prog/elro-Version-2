#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-/opt/pi-receiver/receiver.env}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

BASE_DIR="${BASE_DIR:-/opt/pi-receiver}"
SHARED_DIR="${SHARED_DIR:-$BASE_DIR/shared}"
HOST_DIR="${HOST_DIR:-$BASE_DIR/host}"
STATE_FILE="${STATE_FILE:-$SHARED_DIR/state.json}"
RELOAD_TOKEN_FILE="${RELOAD_TOKEN_FILE:-$SHARED_DIR/reload.token}"
KIOSK_USER="${KIOSK_USER:-maxi}"
DISPLAY_NUM="${DISPLAY_NUM:-:0}"
XAUTHORITY_PATH="${XAUTHORITY_PATH:-/home/$KIOSK_USER/.Xauthority}"
ENABLE_KIOSK="${ENABLE_KIOSK:-1}"
KIOSK_POLL_SECONDS="${KIOSK_POLL_SECONDS:-2}"
DEFAULT_URL="${DEFAULT_URL:-file://$HOST_DIR/blank.html}"
CHROMIUM_BIN="${CHROMIUM_BIN:-auto}"

choose_browser() {
  if [[ "$CHROMIUM_BIN" != "auto" ]]; then
    printf '%s\n' "$CHROMIUM_BIN"
    return
  fi
  if command -v chromium >/dev/null 2>&1; then
    command -v chromium
    return
  fi
  if command -v chromium-browser >/dev/null 2>&1; then
    command -v chromium-browser
    return
  fi
  echo "Chromium not found. Install chromium or chromium-browser." >&2
  exit 1
}

BROWSER_BIN="$(choose_browser)"

read_url() {
  python3 - <<PY
import json
from pathlib import Path
state_path = Path(${STATE_FILE@Q})
default_url = ${DEFAULT_URL@Q}
try:
    if state_path.exists():
        data = json.loads(state_path.read_text(encoding='utf-8'))
        print(data.get('target_url') or default_url)
    else:
        print(default_url)
except Exception:
    print(default_url)
PY
}

wait_for_graphical_session() {
  until [[ -f "$XAUTHORITY_PATH" ]]; do
    sleep 2
  done
  until runuser -u "$KIOSK_USER" -- env DISPLAY="$DISPLAY_NUM" XAUTHORITY="$XAUTHORITY_PATH" xset q >/dev/null 2>&1; do
    sleep 2
  done
}

kill_kiosk_browser() {
  pkill -u "$KIOSK_USER" -f "${BROWSER_BIN}.*--kiosk" 2>/dev/null || true
  pkill -u "$KIOSK_USER" -f "chromium.*--kiosk" 2>/dev/null || true
}

launch_browser() {
  local url
  url="$(read_url)"
  runuser -u "$KIOSK_USER" -- env DISPLAY="$DISPLAY_NUM" XAUTHORITY="$XAUTHORITY_PATH" \
    "$BROWSER_BIN" \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI,VizDisplayCompositor \
    --disable-gpu \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    "$url" >/tmp/pi-receiver-kiosk.log 2>&1 &
}

main() {
  mkdir -p "$SHARED_DIR" "$HOST_DIR"
  if [[ ! -f "$HOST_DIR/blank.html" ]]; then
    cat > "$HOST_DIR/blank.html" <<HTML
<!doctype html><html><body style="margin:0;background:black;"></body></html>
HTML
  fi

  if [[ ! -f "$STATE_FILE" ]]; then
    printf '{\n  "target_url": "%s",\n  "updated_at": "init"\n}\n' "$DEFAULT_URL" > "$STATE_FILE"
  fi
  if [[ ! -f "$RELOAD_TOKEN_FILE" ]]; then
    date --iso-8601=seconds > "$RELOAD_TOKEN_FILE"
  fi

  if [[ "$ENABLE_KIOSK" != "1" ]]; then
    exit 0
  fi

  wait_for_graphical_session
  local last_token=""
  last_token="$(cat "$RELOAD_TOKEN_FILE" 2>/dev/null || true)"

  while true; do
    if [[ -f "$ENV_FILE" ]]; then
      # shellcheck disable=SC1090
      source "$ENV_FILE"
      ENABLE_KIOSK="${ENABLE_KIOSK:-1}"
    fi

    if [[ "$ENABLE_KIOSK" != "1" ]]; then
      kill_kiosk_browser
      exit 0
    fi

    if ! pgrep -u "$KIOSK_USER" -f "${BROWSER_BIN}.*--kiosk" >/dev/null 2>&1 && ! pgrep -u "$KIOSK_USER" -f "chromium.*--kiosk" >/dev/null 2>&1; then
      launch_browser
    fi

    local current_token=""
    current_token="$(cat "$RELOAD_TOKEN_FILE" 2>/dev/null || true)"
    if [[ "$current_token" != "$last_token" ]]; then
      last_token="$current_token"
      kill_kiosk_browser
      sleep 2
    fi

    sleep "$KIOSK_POLL_SECONDS"
  done
}

main "$@"
