from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

STATE_FILE = Path(os.getenv("STATE_FILE", "/data/state.json"))
RELOAD_TOKEN_FILE = Path(os.getenv("RELOAD_TOKEN_FILE", "/data/reload.token"))
ENV_FILE = Path(os.getenv("ENV_FILE", "/config/receiver.env"))
DEFAULT_URL = os.getenv("DEFAULT_URL", os.getenv("HOST_BLANK_URL", "file:///opt/pi-receiver/host/blank.html"))

app = FastAPI(title="Pi Receiver API")
APP = app


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https", "file"}


def read_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"target_url": DEFAULT_URL, "updated_at": now_iso()}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "target_url": DEFAULT_URL,
            "updated_at": now_iso(),
            "warning": "state file was invalid JSON and was reset in memory",
        }


def write_state(url: str) -> dict[str, Any]:
    payload = {"target_url": url, "updated_at": now_iso()}
    ensure_parent(STATE_FILE)
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def trigger_reload(reason: str = "manual") -> dict[str, Any]:
    payload = {"reload_requested_at": now_iso(), "reason": reason}
    ensure_parent(RELOAD_TOKEN_FILE)
    RELOAD_TOKEN_FILE.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def read_env_file() -> dict[str, str]:
    data: dict[str, str] = {}
    if not ENV_FILE.exists():
        return data
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def write_env_file(values: dict[str, str]) -> None:
    existing_lines: list[str] = []
    if ENV_FILE.exists():
        existing_lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    handled = set()
    output: list[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in values:
                output.append(f"{key}={values[key]}")
                handled.add(key)
                continue
        output.append(line)

    for key, value in values.items():
        if key not in handled:
            output.append(f"{key}={value}")

    ensure_parent(ENV_FILE)
    ENV_FILE.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def set_kiosk_enabled(enabled: bool) -> dict[str, Any]:
    write_env_file({"ENABLE_KIOSK": "1" if enabled else "0"})
    return {
        "kiosk_enabled": enabled,
        "env_file": str(ENV_FILE),
        "updated_at": now_iso(),
    }


def get_kiosk_enabled() -> bool:
    return read_env_file().get("ENABLE_KIOSK", "1") == "1"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/state")
def state() -> dict[str, Any]:
    payload = read_state()
    payload["kiosk_enabled"] = get_kiosk_enabled()
    return payload


@app.get("/reload")
def reload_browser() -> dict[str, Any]:
    return trigger_reload("reload-endpoint")


@app.get("/blank")
def blank() -> dict[str, Any]:
    state_payload = write_state(DEFAULT_URL)
    reload_payload = trigger_reload("blank-endpoint")
    return {**state_payload, **reload_payload, "kiosk_enabled": get_kiosk_enabled()}


@app.get("/open")
def open_url(url: str = Query(..., description="Target URL to display")) -> dict[str, Any]:
    if not valid_url(url):
        raise HTTPException(status_code=400, detail="Only http, https and file URLs are allowed")
    state_payload = write_state(url)
    kiosk_payload = set_kiosk_enabled(True)
    reload_payload = trigger_reload("open-endpoint")
    return {**state_payload, **kiosk_payload, **reload_payload}


@app.post("/open-form")
def open_form(url: str = Form(...)) -> JSONResponse:
    if not valid_url(url):
        raise HTTPException(status_code=400, detail="Only http, https and file URLs are allowed")
    state_payload = write_state(url)
    kiosk_payload = set_kiosk_enabled(True)
    reload_payload = trigger_reload("open-form")
    return JSONResponse({**state_payload, **kiosk_payload, **reload_payload})


@app.get("/kiosk/enable")
def kiosk_enable() -> dict[str, Any]:
    kiosk_payload = set_kiosk_enabled(True)
    reload_payload = trigger_reload("kiosk-enable")
    return {**kiosk_payload, **reload_payload}


@app.get("/kiosk/disable")
def kiosk_disable() -> dict[str, Any]:
    kiosk_payload = set_kiosk_enabled(False)
    reload_payload = trigger_reload("kiosk-disable")
    return {**kiosk_payload, **reload_payload}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    current = read_state().get("target_url", DEFAULT_URL)
    return f"""<!DOCTYPE html>
<html>
<head>
<title>Pi Receiver</title>
<style>
body {{
  font-family: Arial, Helvetica, sans-serif;
  background: #ececec;
  color: #111;
}}
.wrap {{
  margin: 20px 0 0 50px;
}}
h1 {{
  display: inline-block;
  margin: 0 20px 0 0;
}}
.top-buttons {{
  display: inline-block;
  vertical-align: top;
}}
.top-buttons button {{
  margin-right: 18px;
}}
.muted {{
  color: #666;
  margin-top: 22px;
  margin-bottom: 14px;
}}
.current {{
  margin-bottom: 18px;
  font-family: monospace;
  word-break: break-all;
}}
label {{
  display: block;
  font-size: 16px;
  margin-bottom: 6px;
}}
input[type=text] {{
  width: 760px;
  max-width: calc(100vw - 140px);
  padding: 10px;
  font-size: 16px;
  box-sizing: border-box;
}}
button {{
  padding: 10px 18px;
  font-size: 16px;
  cursor: pointer;
}}
.open-btn {{
  margin-top: 8px;
}}
.links {{
  margin-top: 34px;
}}
.links a {{
  margin-right: 34px;
}}
</style>
</head>
<body>
<div class="wrap">
  <div>
    <h1>Pi Receiver</h1>
    <div class="top-buttons">
      <button onclick="fetch('/kiosk/enable').then(() => location.reload())">Start</button>
      <button onclick="fetch('/kiosk/disable').then(() => location.reload())">Stop</button>
    </div>
  </div>

  <div class="muted">Current target:</div>
  <div class="current">{current}</div>

  <label for="url">URL</label>
  <input id="url" type="text" value="{current}" placeholder="Enter URL"/>
  <div>
    <button class="open-btn" onclick="openUrl()">Open URL</button>
  </div>

  <div class="links">
    <a href="#" onclick="fetch('/blank').then(() => location.reload()); return false;">Blank</a>
    <a href="#" onclick="fetch('/reload').then(() => location.reload()); return false;">Reload</a>
    <a href="/state" target="_blank">State</a>
    <a href="/health" target="_blank">Health</a>
    <a href="#" onclick="document.getElementById('url').value='https://www.wikipedia.org'; openUrl(); return false;">Wikipedia</a>
    <a href="#" onclick="document.getElementById('url').value='https://example.com'; openUrl(); return false;">Example</a>
  </div>
</div>

<script>
function openUrl(){{
    const url = document.getElementById('url').value;
    fetch('/open?url=' + encodeURIComponent(url))
      .then(() => location.reload());
}}
</script>
</body>
</html>"""
