# Pi Receiver Minimal v3

Diese Version behebt die Probleme aus der ersten ZIP:
- kein harter `/home/pi`-Pfad mehr
- `chromium` statt nur `chromium-browser`
- kein `uvicorn[standard]`, also keine unnötigen Build-Fehler mit `uvloop` / `httptools`
- systemd startet korrekt `app:app`
- `state.json` wird beim Install auf den echten Benutzerpfad angepasst

## Installation auf dem Pi

```bash
cd /home/maxi
unzip -o pi-receiver-minimal-v2-fixed.zip
cd pi-receiver-minimal-v2
chmod +x install_receiver.sh
sudo ./install_receiver.sh
sudo reboot
```

## Danach testen

```bash
systemctl status pi-receiver-api.service --no-pager
curl http://127.0.0.1:8091/health
```

Steuerseite im Browser:

```text
http://PI-IP:8091/
```


Zusätzliche Fixes in v3:
- `python-multipart` ist in den Requirements enthalten
- FastAPI-Instanz ist sowohl als `app` als auch als `APP` verfügbar
