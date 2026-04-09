\
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_DIR="${BASE_DIR:-/opt/pi-receiver}"

sudo mkdir -p "$BASE_DIR/shared" "$BASE_DIR/host"

if [[ -f "$PROJECT_DIR/receiver.env" ]]; then
  sudo cp "$PROJECT_DIR/receiver.env" "$BASE_DIR/receiver.env"
else
  sudo cp "$PROJECT_DIR/receiver.env.example" "$BASE_DIR/receiver.env"
fi

sudo cp "$PROJECT_DIR/host/blank.html" "$BASE_DIR/host/blank.html"

if [[ -f "$PROJECT_DIR/shared_template/state.json" ]]; then
  sudo cp "$PROJECT_DIR/shared_template/state.json" "$BASE_DIR/shared/state.json"
fi

if [[ -f "$PROJECT_DIR/shared_template/reload.token" ]]; then
  sudo cp "$PROJECT_DIR/shared_template/reload.token" "$BASE_DIR/shared/reload.token"
fi

sudo install -m 755 "$PROJECT_DIR/host/start-kiosk.sh" "$BASE_DIR/host/start-kiosk.sh"

SERVICE_FILE="/etc/systemd/system/pi-receiver-kiosk.service"
sudo cp "$PROJECT_DIR/host/pi-receiver-kiosk.service" "$SERVICE_FILE"
sudo systemctl daemon-reload

echo "Host files installed."
echo "Next:"
echo "  sudo docker compose --env-file receiver.env up -d --build"
echo "  sudo systemctl enable --now pi-receiver-kiosk.service"
