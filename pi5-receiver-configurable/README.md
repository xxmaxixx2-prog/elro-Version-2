# Pi Receiver Pi 5 Configurable

This package splits the project into two parts:

- **API in Docker**
- **Chromium kiosk on the Pi 5 host**

Everything important is controlled through **one config file**: `receiver.env`.

## Structure

- `receiver.env.example` – central config template
- `docker-compose.yml` – Docker API service
- `api/` – FastAPI control service
- `host/` – host kiosk scripts and systemd service
- `shared_template/` – initial shared state files

## Why this structure

- Docker is good for the API and config separation.
- The browser kiosk should stay on the host desktop session.
- You can disable kiosk mode later without removing the API.

## Main config values

Copy `receiver.env.example` to `receiver.env` and adjust these values:

- `API_PORT` – external API port on the Pi 5, e.g. `18091`
- `KIOSK_USER` – desktop user, e.g. `maxi`
- `XAUTHORITY_PATH` – usually `/home/maxi/.Xauthority`
- `ENABLE_KIOSK` – `1` or `0`
- `BASE_DIR` – default `/opt/pi-receiver`

## Host install

Run this on the Pi 5 inside the unpacked folder:

```bash
cp receiver.env.example receiver.env
nano receiver.env
chmod +x host/install_host_kiosk.sh host/enable-kiosk.sh host/disable-kiosk.sh
./host/install_host_kiosk.sh
```

The install script copies your local `receiver.env` to `/opt/pi-receiver/receiver.env`.

At minimum check in `receiver.env`:

- `KIOSK_USER=maxi`
- `XAUTHORITY_PATH=/home/maxi/.Xauthority`
- `API_PORT=18091`
- `ENABLE_KIOSK=1`

## Docker API install

In the project folder:

```bash
sudo mkdir -p /opt/pi-receiver/shared /opt/pi-receiver/host
sudo cp shared_template/state.json /opt/pi-receiver/shared/state.json
sudo cp shared_template/reload.token /opt/pi-receiver/shared/reload.token
sudo cp host/blank.html /opt/pi-receiver/host/blank.html
sudo docker compose --env-file receiver.env up -d --build
```

## Start kiosk mode

After the host config is correct:

```bash
sudo systemctl enable --now pi-receiver-kiosk.service
```

## Disable kiosk mode again

Temporary:

```bash
sudo systemctl stop pi-receiver-kiosk.service
```

Persistent with config toggle:

```bash
./host/disable-kiosk.sh
```

Enable again:

```bash
./host/enable-kiosk.sh
```

## API URLs on your Pi 5

Replace the port if you changed it. Default example for your Pi 5:

- `http://192.168.178.54:18091/`
- `http://192.168.178.54:18091/health`
- `http://192.168.178.54:18091/state`
- `http://192.168.178.54:18091/open?url=https://www.wikipedia.org`
- `http://192.168.178.54:18091/blank`
- `http://192.168.178.54:18091/reload`

## Notes

- The API writes to shared files on the host.
- The kiosk service watches the reload token and restarts Chromium when needed.
- If many ports are already used on the Pi 5, just change `API_PORT` in `receiver.env`.
