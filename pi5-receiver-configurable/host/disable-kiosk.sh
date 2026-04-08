#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="${1:-/opt/pi-receiver/receiver.env}"
sudo sed -i 's/^ENABLE_KIOSK=.*/ENABLE_KIOSK=0/' "$ENV_FILE"
sudo systemctl stop pi-receiver-kiosk.service || true
