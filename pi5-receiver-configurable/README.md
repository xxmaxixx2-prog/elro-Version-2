# Pi Receiver Pi 5 Configurable

Dieses Paket ist als **saubere Hauptversion** gedacht:
- **API in Docker**
- **Chromium-Kiosk auf dem Pi-Host**
- Steuerung über **eine zentrale Datei**: `receiver.env`

## Wichtige Punkte
- Die Weboberfläche behält die bisherige Grundstruktur.
- Es kommen **nur zwei zusätzliche Buttons** dazu: **Start** und **Stop**.
- **Open URL** aktiviert den Kiosk automatisch wieder.
- Die API schreibt `ENABLE_KIOSK=1/0` in `receiver.env`.
- Der Host-Service beobachtet weiter `state.json` und `reload.token`.

## Struktur
- `receiver.env.example` – zentrale Konfiguration
- `docker-compose.yml` – Docker-API
- `api/` – FastAPI-Kontrolldienst
- `host/` – Host-Skripte und systemd-Service
- `shared_template/` – initiale State-Dateien

## Schnellstart
```bash
cp receiver.env.example receiver.env
chmod +x host/*.sh
./host/install_host_kiosk.sh
sudo docker compose --env-file receiver.env up -d --build
sudo systemctl enable --now pi-receiver-kiosk.service
```

## Wichtige URLs
- `/` – Weboberfläche
- `/health` – Healthcheck
- `/state` – aktueller Status
- `/open?url=...` – neue Ziel-URL setzen und Kiosk aktivieren
- `/blank` – Blank-Seite
- `/reload` – Browser neu laden
- `/kiosk/enable` – Kiosk einschalten
- `/kiosk/disable` – Kiosk ausschalten
