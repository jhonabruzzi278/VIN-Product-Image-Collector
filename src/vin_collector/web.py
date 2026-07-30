"""Interfaz web sencilla (FastAPI) sobre el mismo pipeline que usa el CLI.

Permite: subir un listado (Excel/CSV/TXT), disparar el procesamiento en segundo
plano, ver el progreso en vivo (leyendo el mismo SQLite que actualiza el pipeline
producto a producto) y descargar/ver el reporte final.
"""

from __future__ import annotations

import shutil
import sys
import threading
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from .config import settings
from .database import Database
from .pipeline import run_pipeline
from .report import generate_report

app = FastAPI(title="VIN Product Image Collector")

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

settings.output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(settings.output_dir)), name="output")

_job_lock = threading.Lock()
_job_state: dict = {"running": False, "filename": None, "error": None}


def _setup_logging_once() -> None:
    if getattr(_setup_logging_once, "_done", False):
        return
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    logger.add(settings.logs_dir / "collector.log", rotation="5 MB", retention=5, level="DEBUG")
    _setup_logging_once._done = True  # type: ignore[attr-defined]


def _run_job(input_path: Path) -> None:
    try:
        run_pipeline(str(input_path))
        generate_report()
    except Exception as exc:  # el hilo de fondo no debe morir en silencio
        logger.exception(f"Job en segundo plano falló: {exc}")
        with _job_lock:
            _job_state["error"] = str(exc)
    finally:
        with _job_lock:
            _job_state["running"] = False


@app.on_event("startup")
def _on_startup() -> None:
    _setup_logging_once()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    db = Database()
    counts = db.counts()
    cobertura = round((counts["encontrados"] / counts["total"]) * 100, 1) if counts["total"] else 0.0
    with _job_lock:
        job = dict(_job_state)
    report_exists = (settings.output_dir / "reporte.html").exists()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "counts": counts,
            "cobertura": cobertura,
            "job": job,
            "report_exists": report_exists,
        },
    )


@app.get("/status.json")
def status():
    db = Database()
    counts = db.counts()
    cobertura = round((counts["encontrados"] / counts["total"]) * 100, 1) if counts["total"] else 0.0
    with _job_lock:
        job = dict(_job_state)
    return JSONResponse({**counts, "cobertura": cobertura, **job})


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    with _job_lock:
        if _job_state["running"]:
            return RedirectResponse("/", status_code=303)

    dest = settings.input_dir / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    with _job_lock:
        _job_state["running"] = True
        _job_state["filename"] = file.filename
        _job_state["error"] = None

    thread = threading.Thread(target=_run_job, args=(dest,), daemon=True)
    thread.start()

    return RedirectResponse("/", status_code=303)
