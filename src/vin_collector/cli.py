"""CLI (Typer) — punto de entrada del sistema."""

from __future__ import annotations

import sys

import typer
from loguru import logger

from .config import settings
from .database import Database
from .pipeline import run_pipeline
from .report import generate_report

app = typer.Typer(add_completion=False, help="VIN Product Image Collector — catálogo con imágenes verificadas.")


def _setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    logger.add(settings.logs_dir / "collector.log", rotation="5 MB", retention=5, level="DEBUG")


@app.command()
def run(
    input_path: str = typer.Argument(..., help="Ruta al Excel/CSV/TXT de productos (ej. input/productos.xlsx)"),
):
    """Ejecuta el flujo completo: importar, enriquecer, buscar, descargar, optimizar y reportar."""
    _setup_logging()
    results, report = run_pipeline(input_path)
    generate_report()
    typer.echo(
        f"\nListo: {report.encontrados}/{report.total} encontrados "
        f"({report.cobertura_pct}% cobertura). Ver output/reporte.html"
    )


@app.command()
def report():
    """Regenera output/catalogo.csv y output/reporte.html a partir de la base de datos actual."""
    _setup_logging()
    csv_path, html_path = generate_report()
    typer.echo(f"Generado:\n  {csv_path}\n  {html_path}")


@app.command()
def status():
    """Muestra el conteo actual de productos en la base de datos."""
    db = Database()
    counts = db.counts()
    cobertura = round((counts["encontrados"] / counts["total"]) * 100, 1) if counts["total"] else 0.0
    typer.echo(
        f"Productos: {counts['total']}  Encontrados: {counts['encontrados']}  "
        f"Pendientes: {counts['pendientes']}  Cobertura: {cobertura}%"
    )


if __name__ == "__main__":
    app()
