#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
  echo "Bitte mit sudo starten: sudo ./install_receiver.sh"
  exit 1
fi

PI_USER="${SUDO_USER:-}"
if [[ -z "$PI_USER" || "$PI_USER" == "root" ]]; then
  PI_USER="$(logname 2>/dev/null || true)"
fi
if [[ -z "$PI_USER" || "$PI_USER" == "root" ]]; then
  echo "Konnte den Zielbenutzer nicht sicher ermitteln. Bitte als normaler Benutzer mit sudo starten."
  exit 1
fi
if ! id "$PI_USER" >/dev/null 2>&1; then
  echo "Benutzer '$PI_USER' existiert nicht."
  exit 1
fi

PI_HOME="$(getent passwd "$PI_USER" | cut -d: -f6)"
PROJECT_SRC_DIR="$(cd "$(dirname "$0")" && pwd)/project"
PROJECT_DST_DIR="$PI_HOME/pi-receiver"
SERVICE_FILE="/etc/systemd/system/pi-receiver-api.service"
GETTY_DIR="/etc/systemd/system/getty@tty1.service.d"
GETTY_FILE="$GETTY_DIR/autologin.conf"
BASH_PROFILE="$PI_HOME/.bash_profile"
BROWSER_PKG="chromium"

if ! apt-cache show "$BROWSER_PKG" >/dev/null 2>&1; then
  if apt-cache show chromium-browser >/dev/null 2>&1; then
    BROWSER_PKG="chromium-browser"
  else
    echo "Kein Chromium-Paket gefunden (chromium / chromium-browser)."
    exit 1
  fi
fi

echo "[1/9] Pakete installieren..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  xserver-xorg \
  x11-xserver-utils \
  xinit \
  openbox \
  "$BROWSER_PKG" \
  unclutter \
  python3-venv \
  ca-certificates

echo "[2/9] Projekt nach $PROJECT_DST_DIR kopieren..."
rm -rf "$PROJECT_DST_DIR"
mkdir -p "$PROJECT_DST_DIR"
cp -R "$PROJECT_SRC_DIR/"* "$PROJECT_DST_DIR/"
chown -R "$PI_USER:$PI_USER" "$PROJECT_DST_DIR"

echo "[3/9] Platzhalter auflösen..."
BLANK_URL="$(python3 - <<PY
from pathlib import Path
print((Path(r"$PROJECT_DST_DIR") / 'blank.html').resolve().as_uri())
PY
)"
sed -i "s|__BLANK_URL__|$BLANK_URL|g" "$PROJECT_DST_DIR/state.json"

echo "[4/9] Python-venv anlegen..."
rm -rf "$PROJECT_DST_DIR/venv"
sudo -u "$PI_USER" python3 -m venv "$PROJECT_DST_DIR/venv"
sudo -u "$PI_USER" "$PROJECT_DST_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$PI_USER" "$PROJECT_DST_DIR/venv/bin/pip" install -r "$PROJECT_DST_DIR/requirements.txt"

echo "[5/9] API systemd-Service schreiben..."
cat > "$SERVICE_FILE" <<EOF2
[Unit]
Description=Pi Receiver API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$PI_USER
Group=$PI_USER
WorkingDirectory=$PROJECT_DST_DIR
ExecStart=$PROJECT_DST_DIR/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8091
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF2

systemctl daemon-reload
systemctl enable --now pi-receiver-api.service

echo "[6/9] Lokales Auto-Login fuer tty1 setzen..."
mkdir -p "$GETTY_DIR"
cat > "$GETTY_FILE" <<EOF2
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $PI_USER --noclear %I \$TERM
EOF2
systemctl daemon-reload
systemctl restart getty@tty1 || true

echo "[7/9] .bash_profile fuer Autostart auf tty1 vorbereiten..."
touch "$BASH_PROFILE"
if grep -q "PI-RECEIVER-AUTOSTART" "$BASH_PROFILE"; then
  sed -i '/# >>> PI-RECEIVER-AUTOSTART >>>/,/# <<< PI-RECEIVER-AUTOSTART <<</d' "$BASH_PROFILE"
fi
cat >> "$BASH_PROFILE" <<EOF2

# >>> PI-RECEIVER-AUTOSTART >>>
if [ -z "\$DISPLAY" ] && [ "\$(tty)" = "/dev/tty1" ]; then
  startx $PROJECT_DST_DIR/xsession.sh -- :0 vt1 -keeptty
  logout
fi
# <<< PI-RECEIVER-AUTOSTART <<<
EOF2
chown "$PI_USER:$PI_USER" "$BASH_PROFILE"

echo "[8/9] xsession.sh ausführbar machen..."
chmod +x "$PROJECT_DST_DIR/xsession.sh"
chown "$PI_USER:$PI_USER" "$PROJECT_DST_DIR/xsession.sh"

echo "[9/9] Installation abgeschlossen."
echo
echo "Prüfen:"
echo "  systemctl status pi-receiver-api.service --no-pager"
echo "  curl http://127.0.0.1:8091/health"
echo
echo "Dann neu starten mit:"
echo "  sudo reboot"
