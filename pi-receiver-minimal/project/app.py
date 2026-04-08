from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

app = FastAPI(title="Pi Receiver API", version="1.1.0")

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "state.json"
BLANK_URL = (BASE_DIR / "blank.html").resolve().as_uri()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state() -> dict[str, Any]:
    return {"target_url": BLANK_URL, "updated_at": now_iso()}


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        data = default_state()
        save_state(data)
        return data
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("state.json ist kein Objekt")
        if not data.get("target_url"):
            data["target_url"] = BLANK_URL
        if not data.get("updated_at"):
            data["updated_at"] = now_iso()
        return data
    except Exception:
        data = default_state()
        save_state(data)
        return data


def save_state(data: dict[str, Any]) -> None:
    STATE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def normalize_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return BLANK_URL
    if raw.startswith(("http://", "https://", "file://", "about:")):
        return raw
    return f"https://{raw}"


def restart_browser() -> None:
    subprocess.run(
        ["pkill", "-f", "chromium|chromium-browser"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def set_target(url: str) -> dict[str, Any]:
    state = load_state()
    state["target_url"] = normalize_url(url)
    state["updated_at"] = now_iso()
    save_state(state)
    restart_browser()
    return state


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/state")
def state() -> JSONResponse:
    return JSONResponse(load_state())


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    state = load_state()
    current = state.get("target_url", BLANK_URL)
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Pi Receiver Control</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 20px;
      background: #111;
      color: #eee;
    }}
    .wrap {{
      max-width: 720px;
      margin: 0 auto;
    }}
    input[type=text] {{
      width: 100%;
      padding: 12px;
      font-size: 16px;
      box-sizing: border-box;
      margin-bottom: 12px;
    }}
    button, a.btn {{
      display: inline-block;
      padding: 12px 16px;
      margin: 6px 6px 6px 0;
      background: #2a7fff;
      color: white;
      text-decoration: none;
      border: 0;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
    }}
    .btn.secondary {{
      background: #555;
    }}
    .card {{
      background: #1c1c1c;
      border-radius: 12px;
      padding: 16px;
      margin-top: 16px;
    }}
    code {{
      word-break: break-all;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Pi Receiver Control</h1>

    <form action="/open-form" method="post">
      <input type="text" name="url" placeholder="https://www.youtube.com/..." value="{current}">
      <button type="submit">Open URL</button>
    </form>

    <div>
      <a class="btn secondary" href="/blank">Black Screen</a>
      <a class="btn secondary" href="/reload">Reload Browser</a>
      <a class="btn secondary" href="/state">Show State (JSON)</a>
      <a class="btn secondary" href="/health">Health</a>
    </div>

    <div class="card">
      <strong>Aktuelle URL:</strong><br>
      <code>{current}</code>
    </div>

    <div class="card">
      <strong>Direkt-Links:</strong><br><br>
      <code>/open?url=https://www.youtube.com</code><br>
      <code>/blank</code><br>
      <code>/reload</code>
    </div>
  </div>
</body>
</html>"""


@app.post("/open-form")
def open_form(url: str = Form(...)) -> RedirectResponse:
    set_target(url)
    return RedirectResponse(url="/", status_code=303)


@app.get("/open")
def open_url(url: str = Query(..., min_length=1)) -> JSONResponse:
    state = set_target(url)
    return JSONResponse(state)


@app.post("/open")
def open_url_post(url: str = Form(...)) -> JSONResponse:
    state = set_target(url)
    return JSONResponse(state)


@app.get("/blank")
def blank() -> JSONResponse:
    state = set_target(BLANK_URL)
    return JSONResponse(state)


@app.post("/blank")
def blank_post() -> JSONResponse:
    state = set_target(BLANK_URL)
    return JSONResponse(state)


@app.get("/reload")
def reload_browser() -> JSONResponse:
    restart_browser()
    return JSONResponse({"status": "reloading"})


@app.post("/reload")
def reload_browser_post() -> JSONResponse:
    restart_browser()
    return JSONResponse({"status": "reloading"})


# compatibility aliases for uvicorn/service variants
APP = app
