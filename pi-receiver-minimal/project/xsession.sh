#!/usr/bin/env bash
set -euo pipefail

cd /home/pi/pi-receiver

xset s off
xset -dpms
xset s noblank

unclutter -idle 0.1 -root &

openbox-session &

sleep 1

while true; do
  URL="$(python3 - <<'PY'
import json
from pathlib import Path
state = Path('/home/pi/pi-receiver/state.json')
try:
    data = json.loads(state.read_text(encoding='utf-8'))
    print(data.get('target_url', 'file:///home/pi/pi-receiver/blank.html'))
except Exception:
    print('file:///home/pi/pi-receiver/blank.html')
PY
)"
  /usr/bin/chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-features=TranslateUI \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    "$URL" || true

  sleep 1
done
