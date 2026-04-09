from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

STATE_FILE = Path(os.getenv("STATE_FILE", "/data/state.json"))
RELOAD_TOKEN_FILE = Path(os.getenv("RELOAD_TOKEN_FILE", "/data/reload.token"))
DEFAULT_URL = os.getenv(
    "DEFAULT_URL",
    os.getenv("HOST_BLANK_URL", "file:///opt/pi-receiver/host/blank.html"),
)
RECEIVER_ENV_FILE = Path(os.getenv("RECEIVER_ENV_FILE", "/opt/pi-receiver/receiver.env"))

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


def read_kiosk_enabled() -> bool | None:
    if not RECEIVER_ENV_FILE.exists():
        return None

    text = RECEIVER_ENV_FILE.read_text(encoding="utf-8")
    match = re.search(r"^ENABLE_KIOSK=(.+)$", text, flags=re.MULTILINE)
    if not match:
        return None

    value = match.group(1).strip().strip('"').strip("'")
    return value == "1"


def set_kiosk_enabled(enabled: bool) -> dict[str, Any]:
    ensure_parent(RECEIVER_ENV_FILE)
    existing = RECEIVER_ENV_FILE.read_text(encoding="utf-8") if RECEIVER_ENV_FILE.exists() else ""
    replacement = f"ENABLE_KIOSK={'1' if enabled else '0'}"

    if re.search(r"^ENABLE_KIOSK=.*$", existing, flags=re.MULTILINE):
        updated = re.sub(r"^ENABLE_KIOSK=.*$", replacement, existing, flags=re.MULTILINE)
    else:
        suffix = "\n" if existing and not existing.endswith("\n") else ""
        updated = f"{existing}{suffix}{replacement}\n"

    RECEIVER_ENV_FILE.write_text(updated, encoding="utf-8")
    return {
        "kiosk_enabled": enabled,
        "receiver_env": str(RECEIVER_ENV_FILE),
        "updated_at": now_iso(),
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "kiosk_enabled": read_kiosk_enabled(),
        "receiver_env": str(RECEIVER_ENV_FILE),
    }


@app.get("/state")
def state() -> dict[str, Any]:
    payload = read_state()
    payload["kiosk_enabled"] = read_kiosk_enabled()
    return payload


@app.get("/reload")
def reload_browser() -> dict[str, Any]:
    return trigger_reload("reload-endpoint")


@app.get("/blank")
def blank() -> dict[str, Any]:
    state_payload = write_state(DEFAULT_URL)
    reload_payload = trigger_reload("blank-endpoint")
    return {**state_payload, **reload_payload, "kiosk_enabled": read_kiosk_enabled()}


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
    return f"""
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Pi Receiver</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; }}
    .title-row {{ display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }}
    .title-row h1 {{ margin: 0; }}
    input[type=text] {{ width: 100%; padding: 0.75rem; font-size: 1rem; box-sizing: border-box; }}
    button, a.btn {{ display: inline-block; margin: 0.5rem 0.5rem 0 0; padding: 0.75rem 1rem; font-size: 1rem; text-decoration: none; cursor: pointer; }}
    code {{ word-break: break-all; }}
    .muted {{ color: #666; }}
  </style>
</head>
<body>
  <div class=\"title-row\">
    <h1>Pi Receiver</h1>
    <button type=\"button\" onclick=\"kioskAction('/kiosk/enable')\">▶ Start Kiosk</button>
    <button type=\"button\" onclick=\"kioskAction('/kiosk/disable')\">⏹ Stop Kiosk</button>
  </div>

  <p class=\"muted\">Current target:</p>
  <p><code>{current}</code></p>

  <form onsubmit=\"openUrl(event)\">
    <label for=\"url\">URL</label>
    <input id=\"url\" name=\"url\" type=\"text\" value=\"{current}\" placeholder=\"https://www.wikipedia.org\" required>
    <button type=\"submit\">Open URL</button>
  </form>

  <p>
    <a class=\"btn\" href=\"/blank\">Blank</a>
    <a class=\"btn\" href=\"/reload\">Reload</a>
    <a class=\"btn\" href=\"/state\">State</a>
    <a class=\"btn\" href=\"/health\">Health</a>
    <a class=\"btn\" href=\"/open?url=https://www.wikipedia.org\">Wikipedia</a>
    <a class=\"btn\" href=\"/open?url=https://example.com\">Example</a>
  </p>

  <script>
    async function kioskAction(path) {{
      await fetch(path);
      window.location.reload();
    }}

    async function openUrl(event) {{
      event.preventDefault();
      const url = document.getElementById('url').value;
      await fetch('/open?url=' + encodeURIComponent(url));
      window.location.reload();
    }}
  </script>
</body>
</html>
"""
