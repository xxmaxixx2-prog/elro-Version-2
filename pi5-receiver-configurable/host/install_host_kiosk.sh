#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_BASE="${1:-/opt/pi-receiver}"
TARGET_HOST="$TARGET_BASE/host"
TARGET_SHARED="$TARGET_BASE/shared"
ENV_TARGET="$TARGET_BASE/receiver.env"

sudo mkdir -p "$TARGET_HOST" "$TARGET_SHARED"
sudo cp "$SCRIPT_DIR/start-kiosk.sh" "$TARGET_HOST/start-kiosk.sh"
sudo cp "$SCRIPT_DIR/blank.html" "$TARGET_HOST/blank.html"
sudo chmod +x "$TARGET_HOST/start-kiosk.sh"

if [[ -f "$ROOT_DIR/receiver.env" ]]; then
  sudo cp "$ROOT_DIR/receiver.env" "$ENV_TARGET"
elif [[ ! -f "$ENV_TARGET" ]]; then
  sudo cp "$ROOT_DIR/receiver.env.example" "$ENV_TARGET"
fi

if [[ ! -f "$TARGET_SHARED/state.json" ]]; then
  sudo tee "$TARGET_SHARED/state.json" >/dev/null <<JSON
{
  "target_url": "file://$TARGET_HOST/blank.html",
  "updated_at": "init"
}
JSON
fi

if [[ ! -f "$TARGET_SHARED/reload.token" ]]; then
  date --iso-8601=seconds | sudo tee "$TARGET_SHARED/reload.token" >/dev/null
fi

sudo cp "$SCRIPT_DIR/pi-receiver-kiosk.service" /etc/systemd/system/pi-receiver-kiosk.service
sudo systemctl daemon-reload

echo

echo "Host kiosk files installed to: $TARGET_BASE"
echo "Edit $ENV_TARGET before enabling the kiosk service."
echo "Then run: sudo systemctl enable --now pi-receiver-kiosk.service"
