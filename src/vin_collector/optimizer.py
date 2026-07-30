"""Módulo 8 — Optimizador: genera WebP, miniaturas en varios tamaños y (opcional) PNG transparente."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from PIL import Image

from .config import settings


def optimize_image(source_path: str | Path) -> dict[str, str]:
    """A partir de la imagen original genera:
    - WebP optimizado (calidad 85)
    - Miniaturas JPEG/WebP en los tamaños de settings.thumbnail_sizes
    - PNG con fondo transparente si `rembg` está instalado (opcional, se omite si no)

    Devuelve un dict {nombre_variante: ruta_local}.
    """
    source_path = Path(source_path)
    variants: dict[str, str] = {}

    try:
        img = Image.open(source_path).convert("RGB")
    except Exception as exc:
        logger.warning(f"No se pudo abrir {source_path} para optimizar: {exc}")
        return variants

    stem = source_path.stem

    webp_path = settings.images_dir / f"{stem}.webp"
    img.save(webp_path, "WEBP", quality=85, method=6)
    variants["webp"] = str(webp_path)

    for size in settings.thumbnail_sizes:
        thumb = img.copy()
        thumb.thumbnail((size, size), Image.LANCZOS)
        thumb_path = settings.thumbnails_dir / f"{stem}_{size}.webp"
        thumb.save(thumb_path, "WEBP", quality=80, method=6)
        variants[f"thumb_{size}"] = str(thumb_path)

    transparent_path = _try_remove_background(source_path, stem)
    if transparent_path:
        variants["png_transparente"] = str(transparent_path)

    logger.info(f"{len(variants)} variantes generadas para {source_path.name}")
    return variants


def _try_remove_background(source_path: Path, stem: str) -> Path | None:
    try:
        from rembg import remove  # dependencia opcional, no listada en requirements por defecto
    except ImportError:
        return None

    try:
        input_bytes = source_path.read_bytes()
        output_bytes = remove(input_bytes)
        dest = settings.images_dir / f"{stem}_transparent.png"
        dest.write_bytes(output_bytes)
        return dest
    except Exception as exc:
        logger.debug(f"rembg falló, se omite PNG transparente: {exc}")
        return None
