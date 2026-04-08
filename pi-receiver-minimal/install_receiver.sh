#!/usr/bin/env bash
set -euo pipefail

PI_USER="${SUDO_USER:-pi}"
PI_HOME="$(getent passwd "$PI_USER" | cut -d: -f6)"
PROJECT_SRC_DIR="$(cd "$(dirname "$0")" && pwd)/project"
PROJECT_DST_DIR="$PI_HOME/pi-receiver"
SERVICE_FILE="/etc/systemd/system/pi-receiver-api.service"
GETTY_DIR="/etc/systemd/system/getty@tty1.service.d"
GETTY_FILE="$GETTY_DIR/autologin.conf"
BASH_PROFILE="$PI_HOME/.bash_profile"

if [[ "$EUID" -ne 0 ]]; then
  echo "Bitte mit sudo starten: sudo ./install_receiver.sh"
  exit 1
fi

if ! id "$PI_USER" >/dev/null 2>&1; then
  echo "Benutzer '$PI_USER' existiert nicht."
  exit 1
fi

echo "[1/8] Pakete installieren..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  xserver-xorg \
  x11-xserver-utils \
  xinit \
  openbox \
  chromium-browser \
  unclutter \
  python3-venv

echo "[2/8] Projekt nach $PROJECT_DST_DIR kopieren..."
rm -rf "$PROJECT_DST_DIR"
mkdir -p "$PROJECT_DST_DIR"
cp -R "$PROJECT_SRC_DIR/"* "$PROJECT_DST_DIR/"
chown -R "$PI_USER:$PI_USER" "$PROJECT_DST_DIR"

echo "[3/8] Python-venv anlegen..."
sudo -u "$PI_USER" python3 -m venv "$PROJECT_DST_DIR/venv"
sudo -u "$PI_USER" "$PROJECT_DST_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$PI_USER" "$PROJECT_DST_DIR/venv/bin/pip" install -r "$PROJECT_DST_DIR/requirements.txt"

echo "[4/8] API systemd-Service schreiben..."
cat > "$SERVICE_FILE" <<EOF
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
EOF

systemctl daemon-reload
systemctl enable --now pi-receiver-api.service

echo "[5/8] Lokales Auto-Login fuer tty1 setzen..."
mkdir -p "$GETTY_DIR"
cat > "$GETTY_FILE" <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $PI_USER --noclear %I \$TERM
EOF

systemctl daemon-reload

echo "[6/8] .bash_profile fuer Autostart auf tty1 vorbereiten..."
touch "$BASH_PROFILE"
if ! grep -q "PI-RECEIVER-AUTOSTART" "$BASH_PROFILE"; then
cat >> "$BASH_PROFILE" <<'EOF'

# >>> PI-RECEIVER-AUTOSTART >>>
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx /home/pi/pi-receiver/xsession.sh -- :0 vt1 -keeptty
  logout
fi
# <<< PI-RECEIVER-AUTOSTART <<<
EOF
fi
chown "$PI_USER:$PI_USER" "$BASH_PROFILE"

echo "[7/8] xsession.sh ausführbar machen..."
chmod +x "$PROJECT_DST_DIR/xsession.sh"
chown "$PI_USER:$PI_USER" "$PROJECT_DST_DIR/xsession.sh"

echo "[8/8] Fertig."
echo
echo "Jetzt neu starten mit:"
echo "  sudo reboot"
echo
echo "Nach dem Neustart:"
echo "  Steuerseite: http://<PI-IP>:8091"
echo "  Health:      http://<PI-IP>:8091/health"
