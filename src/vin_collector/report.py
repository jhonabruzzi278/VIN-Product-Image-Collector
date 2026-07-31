"""Módulo 12 — Reporte final: catalogo.csv + reporte.html con métricas de cobertura."""

from __future__ import annotations

import csv
from datetime import datetime

from jinja2 import Template
from loguru import logger

from .config import settings
from .database import Database

CSV_HEADERS = [
    "sku", "nombre_original", "nombre_normalizado", "marca", "categoria", "ean",
    "proveedor", "status", "imagen_local", "fuente", "ancho", "alto", "score",
    "ai_verified", "ai_confidence",
]

HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Reporte — VIN Product Image Collector</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 2rem; background: #f7f7f8; color: #1a1a1a; }
  h1 { margin-bottom: .25rem; }
  .subtitle { color: #666; margin-top: 0; }
  .stats { display: flex; gap: 1rem; margin: 1.5rem 0; }
  .stat { background: white; border-radius: 8px; padding: 1rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  .stat .value { font-size: 1.8rem; font-weight: 700; }
  .stat .label { color: #666; font-size: .85rem; }
  table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
  th, td { text-align: left; padding: .5rem .75rem; border-bottom: 1px solid #eee; font-size: .9rem; vertical-align: middle; }
  th { background: #fafafa; position: sticky; top: 0; }
  td.image-cell { text-align: center; }
  a.thumb-link { display: inline-block; }
  img.thumb {
    width: 140px; height: 140px; object-fit: contain; border: 1px solid #eee;
    border-radius: 8px; background: white; display: block; transition: transform .15s ease, box-shadow .15s ease;
  }
  a.thumb-link:hover img.thumb { transform: scale(1.08); box-shadow: 0 4px 14px rgba(0,0,0,.15); }
  a.dl-btn {
    display: inline-flex; align-items: center; gap: .3rem; margin-top: .5rem; padding: .3rem .7rem;
    background: #111827; color: white; border-radius: 6px; font-size: .78rem; font-weight: 600;
    text-decoration: none;
  }
  a.dl-btn:hover { background: #2563eb; }
  .badge { padding: .15rem .5rem; border-radius: 999px; font-size: .75rem; font-weight: 600; }
  .badge.encontrado { background: #dcfce7; color: #166534; }
  .badge.no_encontrado { background: #fee2e2; color: #991b1b; }
  .badge.requiere_revision { background: #fef9c3; color: #854d0e; }
  .badge.pendiente { background: #e5e7eb; color: #374151; }
</style>
</head>
<body>
  <h1>VIN Product Image Collector</h1>
  <p class="subtitle">Reporte generado el {{ generado_en }}</p>

  <div class="stats">
    <div class="stat"><div class="value">{{ total }}</div><div class="label">Productos</div></div>
    <div class="stat"><div class="value">{{ encontrados }}</div><div class="label">Encontrados</div></div>
    <div class="stat"><div class="value">{{ pendientes }}</div><div class="label">Pendientes</div></div>
    <div class="stat"><div class="value">{{ cobertura }}%</div><div class="label">Cobertura</div></div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Imagen</th><th>SKU</th><th>Nombre</th><th>Marca</th><th>Categoría</th>
        <th>Estado</th><th>Score</th><th>IA</th><th>Fuente</th>
      </tr>
    </thead>
    <tbody>
      {% for p in products %}
      <tr>
        <td class="image-cell">
          {% if p.local_path %}
          <a class="thumb-link" href="{{ p.local_path }}" target="_blank" rel="noopener">
            <img class="thumb" src="{{ p.local_path }}" loading="lazy">
          </a>
          <br>
          <a class="dl-btn" href="{{ p.local_path }}" download>⬇ Descargar</a>
          {% endif %}
        </td>
        <td>{{ p.sku or "" }}</td>
        <td>{{ p.nombre_normalizado }}</td>
        <td>{{ p.marca or "" }}</td>
        <td>{{ p.categoria or "" }}</td>
        <td><span class="badge {{ p.status }}">{{ p.status }}</span></td>
        <td>{{ p.score or "" }}</td>
        <td>{% if p.ai_verified is not none %}{{ "Sí" if p.ai_verified else "No" }} ({{ p.ai_confidence }}){% endif %}</td>
        <td>{% if p.source_url %}<a href="{{ p.source_url }}" target="_blank" rel="noopener">enlace</a>{% endif %}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""
)


def _row_for_template(row) -> dict:
    """Normaliza local_path a una ruta relativa "images/<archivo>" servible por HTTP/HTML.

    Se recalcula a partir del nombre de archivo (no de relative_to) porque la misma
    base SQLite puede compartirse entre el host y un contenedor Docker (vía volumen),
    y cada entorno escribe rutas absolutas con una raíz de filesystem distinta
    (ej. "C:\\...\\output\\images\\x.png" en Windows vs "/app/output/images/x.png" en
    el contenedor). Todas las imágenes viven siempre en output/images/, así que el
    nombre de archivo es suficiente y es portable entre entornos.
    """
    data = dict(row)
    local_path = data.get("local_path")
    if local_path:
        # PosixPath no separa por "\": normaliza antes de extraer el nombre de archivo
        # para que rutas Windows escritas por el host (via el mismo SQLite compartido
        # por volumen) también se resuelvan correctamente dentro del contenedor Linux.
        filename = local_path.replace("\\", "/").rsplit("/", 1)[-1]
        data["local_path"] = f"images/{filename}"
    return data


def generate_report(db: Database | None = None) -> tuple[str, str]:
    """Genera output/catalogo.csv y output/reporte.html. Devuelve las rutas generadas."""
    db = db or Database()
    rows = db.all_products_with_images()
    counts = db.counts()

    csv_path = settings.output_dir / "catalogo.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        for r in rows:
            writer.writerow([
                r["sku"], r["nombre_original"], r["nombre_normalizado"], r["marca"],
                r["categoria"], r["ean"], r["proveedor"], r["status"], r["local_path"],
                r["source_url"], r["width"], r["height"], r["score"],
                r["ai_verified"], r["ai_confidence"],
            ])

    html_path = settings.output_dir / "reporte.html"
    template_rows = [_row_for_template(r) for r in rows]
    html = HTML_TEMPLATE.render(
        generado_en=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total=counts["total"],
        encontrados=counts["encontrados"],
        pendientes=counts["pendientes"],
        cobertura=round((counts["encontrados"] / counts["total"]) * 100, 1) if counts["total"] else 0,
        products=template_rows,
    )
    html_path.write_text(html, encoding="utf-8")

    logger.info(f"Reporte generado: {html_path.name}, {csv_path.name}")
    return str(csv_path), str(html_path)
