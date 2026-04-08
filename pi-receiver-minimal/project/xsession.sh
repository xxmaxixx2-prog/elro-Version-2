#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

BROWSER_BIN="$(command -v chromium || command -v chromium-browser || true)"
if [[ -z "$BROWSER_BIN" ]]; then
  echo "Kein Chromium-Browser gefunden (chromium / chromium-browser)." >&2
  sleep 10
  exit 1
fi

xset s off || true
xset -dpms || true
xset s noblank || true

if command -v unclutter >/dev/null 2>&1; then
  unclutter -idle 0.1 -root &
fi

if command -v openbox-session >/dev/null 2>&1; then
  openbox-session &
fi

sleep 1

read_url() {
  python3 - "$SCRIPT_DIR" <<'PY'
import json
import sys
from pathlib import Path

base = Path(sys.argv[1]).resolve()
blank = (base / 'blank.html').resolve().as_uri()
state = base / 'state.json'

try:
    data = json.loads(state.read_text(encoding='utf-8'))
    print(data.get('target_url') or blank)
except Exception:
    print(blank)
PY
}

while true; do
  URL="$(read_url)"
  "$BROWSER_BIN" \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    --no-first-run \
    --disable-component-update \
    "$URL" || true

  sleep 1
done
