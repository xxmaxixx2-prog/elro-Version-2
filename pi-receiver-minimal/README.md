# Pi Receiver Minimal

Minimal-Architektur für einen Raspberry Pi (auch Pi Zero 2 W), der **nur Bild anzeigt**:
- Vollbild/Kiosk ohne Taskleiste
- SSH bleibt normal erreichbar
- Steuerung über Handy/LAN-Webseite
- URL ändern, Schwarzbild, Reload
- Kein Docker nötig
- Kein DevTools-Port, kein xdotool, kein Overengineering

## Ziel
Der Pi ist **nur ein Anzeige-Client**.  
Das Handy oder dein Homelab schickt nur Befehle wie:
- öffne URL
- öffne YouTube-Link
- schwarz
- reload

Die eigentliche Darstellung macht Chromium lokal im Kiosk-Modus.

## Architektur

1. `tty1` meldet den Benutzer `pi` automatisch lokal an.
2. `.bash_profile` startet **nur auf tty1** automatisch `startx`.
3. `xsession.sh` startet:
   - X
   - Openbox
   - unclutter
   - Chromium im Kiosk-Modus
4. Chromium läuft in einer Schleife:
   - beendet man Chromium, startet es neu
   - dabei liest es die aktuelle Ziel-URL aus `state.json`
5. Die lokale API (`app.py`) ändert `state.json` und beendet Chromium.
6. Die Schleife startet Chromium sofort mit der neuen URL neu.

Dadurch brauchst du:
- keine Taskleiste
- keine Maus
- keine Tabs
- keinen komplizierten Fernzugriff auf den Browser

## Was diese ZIP **nicht** löst
- DRM-Sonderfälle wie Netflix/Widevine
- Audio-Routing-Spezialfälle
- Nginx Proxy Manager
- Miracast/AirPlay
- HDMI/AV/RF-Feintuning am Bildrand

Diese ZIP ist die **saubere Minimalbasis**.

---

# Exakte Installation

## 1) ZIP auf den Pi kopieren
Beispiel:
```bash
scp pi-receiver-minimal.zip pi@PI-IP:/home/pi/
```

## 2) Auf dem Pi entpacken
```bash
cd /home/pi
unzip pi-receiver-minimal.zip
cd pi-receiver-minimal
```

## 3) Installer starten
```bash
chmod +x install_receiver.sh
sudo ./install_receiver.sh
```

## 4) Pi neu starten
```bash
sudo reboot
```

Nach dem Neustart:
- der Pi bootet
- `pi` wird lokal auf `tty1` automatisch angemeldet
- X startet
- Chromium startet im Vollbild
- SSH bleibt normal nutzbar

---

# Was der Installer genau macht

## A. Pakete installieren
Installiert:
- `xserver-xorg`
- `x11-xserver-utils`
- `xinit`
- `openbox`
- `chromium-browser`
- `unclutter`
- `python3-venv`

Warum:
- X + Chromium = Vollbildanzeige
- Openbox = leichter Fenstermanager ohne unnötige Desktop-UI
- unclutter = Mauszeiger ausblenden
- venv = lokale Python-Umgebung für die API

## B. Projekt nach `/home/pi/pi-receiver` kopieren
Dort liegen danach:
- `app.py`
- `xsession.sh`
- `blank.html`
- `state.json`
- `requirements.txt`

## C. Python-Umgebung anlegen
- venv wird erzeugt
- FastAPI + uvicorn werden installiert

## D. Lokale API als systemd-Service aktivieren
Service:
- `pi-receiver-api.service`

Nach dem Boot läuft die API auf:
- `http://PI-IP:8091`

## E. Lokales Auto-Login für tty1 setzen
Es wird ein systemd-Override für `getty@tty1` angelegt.

Das betrifft nur den **lokalen Konsolen-Login** auf dem Pi selbst.

## F. X nur auf tty1 automatisch starten
Es wird ein Block in `/home/pi/.bash_profile` eingetragen:
- startet **nur** wenn kein `DISPLAY` gesetzt ist
- startet **nur** auf `/dev/tty1`

Dadurch wird **nicht** jeder SSH-Login zu einer GUI-Session.

---

# Wichtige URLs

## Steuerseite im LAN
```text
http://PI-IP:8091
```

## Health-Check
```text
http://PI-IP:8091/health
```

## Aktueller Zustand
```text
http://PI-IP:8091/state
```

## Direkt URL öffnen
```text
http://PI-IP:8091/open?url=https://www.youtube.com
```

## Schwarzbild
```text
http://PI-IP:8091/blank
```

## Browser neu laden
```text
http://PI-IP:8091/reload
```

---

# Bedienung per Handy

## Variante 1: Steuerseite aufrufen
Auf dem Handy im selben LAN:
```text
http://PI-IP:8091
```

Dann:
- URL eintragen
- Open drücken
- oder Blank / Reload

## Variante 2: Direkte Links bauen
Beispiele:
```text
http://PI-IP:8091/open?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

```text
http://PI-IP:8091/open?url=https://example.com
```

---

# SSH bleibt erhalten

Warum?
- SSH ist ein separater Systemdienst
- die GUI startet nur lokal auf `tty1`
- `.bash_profile` prüft explizit auf `tty1`

Das bedeutet:
- `ssh pi@PI-IP` geht weiter
- du kannst per SSH Dateien ändern
- du kannst Chromium beenden
- du kannst rebooten

---

# Nützliche SSH-Befehle

## API-Logs ansehen
```bash
journalctl -u pi-receiver-api.service -f
```

## API neu starten
```bash
sudo systemctl restart pi-receiver-api.service
```

## Chromium hart beenden
```bash
pkill -f chromium || true
```

Danach startet die Kiosk-Schleife Chromium automatisch neu.

## Pi neu starten
```bash
sudo reboot
```

---

# Bild/HDMI-Hinweis

Dein PC-Screenshot zeigt:
- Desktop 640×480
- aktive Signallösung 720×480
- 60 Hz

Das passt grundsätzlich zu einem HDMI→AV→RF-Weg.

Falls dein Pi mit dem Konverter später ein abgeschnittenes Bild hat, ist das **separates Display-Tuning**.  
Diese ZIP ändert **nicht automatisch** `/boot/firmware/config.txt`, weil solche Optionen je nach Raspberry Pi OS / Treiberpfad unterschiedlich wirken können.

---

# Dateistruktur

- `install_receiver.sh`  
  Hauptinstaller. Einmal mit `sudo` starten.

- `project/app.py`  
  Kleine lokale API + Handy-Steuerseite.

- `project/xsession.sh`  
  Startet Openbox, blendet den Cursor aus und hält Chromium im Kiosk-Modus am Leben.

- `project/blank.html`  
  Einfaches Schwarzbild.

- `project/state.json`  
  Aktuelle Ziel-URL.

- `project/requirements.txt`  
  Python-Abhängigkeiten.

---

# Rückbau

## API stoppen und deaktivieren
```bash
sudo systemctl disable --now pi-receiver-api.service
```

## Auto-Login-Override löschen
```bash
sudo rm -rf /etc/systemd/system/getty@tty1.service.d
sudo systemctl daemon-reload
sudo systemctl restart getty@tty1
```

## .bash_profile-Block entfernen
Den Block zwischen:
- `# >>> PI-RECEIVER-AUTOSTART >>>`
- `# <<< PI-RECEIVER-AUTOSTART <<<`
aus `/home/pi/.bash_profile` löschen.

## Projektordner löschen
```bash
rm -rf /home/pi/pi-receiver
```
