Pi Receiver – Retro TV Kiosk (ELRO)

Ein Raspberry Pi-basierter Receiver, der Web-Inhalte (YouTube, GIFs, Seiten) auf einem alten ELRO Fernseher über Kiosk-Modus darstellt.

_________________________________________________________________________________________________________________
Konzept
Steuerung über Webinterface (Start / Stop / URL)
Anzeige im Chromium Kiosk-Modus
Ausgabe auf alten Fernseher (PAL / niedrige Auflösung)
Inhalte werden remote gesteuert (Browser → Pi)
Weboberfläche
<img width="924" height="368" alt="image" src="https://github.com/user-attachments/assets/b72397b9-3af9-41a4-87b3-4aaa0b427e40" />


_________________________________________________________________________________________________________________
Beispiel:

URL eingeben
„Open URL“ starten
Kiosk automatisch aktivieren
Start / Stop Buttons für Kontrolle

Unterstützt:

YouTube Links
GIFs (z. B. Retro / Pixel Stil)
einfache Webseiten
Empfohlene Inhalte

Retro-GIFs (sehr performant):

https://64.media.tumblr.com/d7764ed59f903ab86ba55f2e16cdbe15/tumblr_oyikjnTegs1uiwrneo1_500.gif

Empfohlen:

8-bit / 16-bit / 32-bit / 64-bit Stil
niedrige Auflösung
wenig Bewegung → stabiler auf alter Hardware
Zielgerät (ELRO Fernseher)
Signal über HDMI -> AV -> RF Modulator
Anzeige:
PAL (~576i)
oft Schwarz-Weiß
begrenzte Schärfe
Performance Settings (sehr wichtig)

Für stabile Darstellung:

Auflösung:

640x480

Frequenz:

59.9 Hz
Skalierung:
→ niedrig halten

Warum:

reduziert CPU/GPU Last
verhindert Lag & Abstürze
stabilisiert alte Hardware-Ausgabe
_________________________________________________________________________________________________________________
Architektur
Browser (Remote)
   ↓
FastAPI (Docker)
   ↓
receiver.env
   ↓
Host Script (Kiosk)
   ↓
Chromium (Fullscreen)
   ↓
HDMI → AV → RF → TV
_________________________________________________________________________________________________________________
Ich nutze folgende Kette:

HDMI → HDMI2AV (PAL) → AV → RF Modulator → Fernseher
🔧 Einstellungen & Hardware
HDMI2AV: auf PAL
RF Modulator (AV → RF):
sendet auf UHF Kanal 21
unterstützt nur Kanal 21–67
(Man braucht für den RF Modulator eine Antenne nach Wahl oder eine Büroklammer :^) )
Fernseher Einstellungen

Empfang:
CH1 (vorderer Schalter, erster Slot)
Modus:
UHF (rechter Schalter ganz rechts)
Feinabstimmung:
Drehregler auf UHF Kanal 21 einstellen
(oder den Kanal, den der Modulator sendet)

WICHTIG
Der RF Modulator sendet nur im Bereich UHF 21–67
Der Fernseher / Monitor muss diese Kanäle unterstützen

Funktioniert typischerweise bei:
-alten Überwachungsmonitoren
-Camping-/Portable TVs (wie dein ELRO)

Falls kein Signal kommt:

prüfen ob wirklich UHF aktiv ist
Kanalbereich checken (21–67)
alternativ:
anderes Antennenkabel
oder Gerät mit passendem Tuner verwenden
_________________________________________________________________________________________________________________
 Features
Start / Stop Kiosk
URL remote setzen
Auto-Kiosk bei „Open URL“
einfache Websteuerung
Docker + Host getrennt
_________________________________________________________________________________________________________________
 Projektstruktur
pi5-receiver-configurable/
api/                    
      # FastAPI Backend
host/                  
      # Kiosk Scripts (Start/Stop)
docker-compose.yml
receiver.env            
      # Steuerung (ENABLE_KIOSK etc.)
shared/                
      # State / Daten


Nutzung
cd ~/elro-Version-2/pi5-receiver-configurable
sudo docker compose --env-file receiver.env up -d --build
sudo systemctl restart pi-receiver-kiosk.service

Webinterface:

http://<PI-IP>:18091


_________________________________________________________________________________________________________________
Continue:

Tipps
GIFs > Videos (weniger Last)
YouTube nur bei stabiler Verbindung
kurze Inhalte vermeiden Hänger
lieber einfache Seiten statt komplexe Apps

Ideen / Ausbau
Statusanzeige im UI (AN/AUS)
Preset Buttons (YouTube, Cam, Retro)
Auto-Rotation von Inhalten
Remote Zugriff (VPN)





