
from fastapi import FastAPI
import subprocess
import json
from pathlib import Path

APP = FastAPI()

STATE_FILE = Path("/home/maxi/pi-receiver/state.json")

@APP.get("/health")
def health():
    return {"status": "ok"}

@APP.get("/state")
def state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"target_url": None}

@APP.get("/open")
def open_url(url: str):
    STATE_FILE.write_text(json.dumps({"target_url": url}))
    subprocess.run(["pkill", "-f", "chromium"])
    return {"status": "opened", "url": url}

@APP.get("/blank")
def blank():
    STATE_FILE.write_text(json.dumps({"target_url": "file:///home/maxi/pi-receiver/blank.html"}))
    subprocess.run(["pkill", "-f", "chromium"])
    return {"status": "blank"}

@APP.get("/reload")
def reload():
    subprocess.run(["pkill", "-f", "chromium"])
    return {"status": "reloaded"}

# NEW KIOSK CONTROL

@APP.get("/kiosk/enable")
def kiosk_enable():
    subprocess.run(["sudo", "systemctl", "start", "pi-receiver-kiosk.service"])
    return {"status": "kiosk started"}

@APP.get("/kiosk/disable")
def kiosk_disable():
    subprocess.run(["sudo", "systemctl", "stop", "pi-receiver-kiosk.service"])
    return {"status": "kiosk stopped"}

app = APP
