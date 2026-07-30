"""Módulo 7 — Descarga de la imagen ganadora y registro de su procedencia.

Incluye deduplicación por hash de contenido: si la misma imagen (bytes idénticos)
ya fue descargada para otro producto, se descarta y se prueba el siguiente candidato.
"""

from __future__ import annotations

import hashlib
import json
import re

import httpx
from loguru import logger

from .config import settings
from .models import DownloadedImage, ImageCandidate, Product
from .ranking import refine_score_with_bytes

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9_\-]+")
_HASHES_PATH = settings.cache_dir / "image_hashes.json"


def _load_hashes() -> set[str]:
    if _HASHES_PATH.exists():
        return set(json.loads(_HASHES_PATH.read_text(encoding="utf-8")))
    return set()


def _save_hashes(hashes: set[str]) -> None:
    _HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _HASHES_PATH.write_text(json.dumps(sorted(hashes)), encoding="utf-8")


def slugify(name: str) -> str:
    name = name.strip().upper().replace(" ", "_")
    name = _SAFE_CHARS.sub("", name)
    return name or "PRODUCTO"


def _guess_extension(url: str, content_type: str | None) -> str:
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if url.lower().split("?")[0].endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    if content_type:
        if "png" in content_type:
            return ".png"
        if "webp" in content_type:
            return ".webp"
        if "gif" in content_type:
            return ".gif"
    return ".jpg"


def download_best_image(
    product: Product,
    candidates: list[ImageCandidate],
    client: httpx.Client | None = None,
) -> DownloadedImage | None:
    """Descarga, refina el puntaje con los bytes reales y guarda la primera imagen aceptable."""
    own_client = client is None
    client = client or httpx.Client(
        timeout=settings.http_timeout_seconds,
        headers={"User-Agent": settings.request_user_agent},
        follow_redirects=True,
    )

    known_hashes = _load_hashes()

    try:
        for candidate in candidates:
            try:
                resp = client.get(candidate.url)
                resp.raise_for_status()
            except Exception as exc:
                logger.debug(f"Descarga fallida para {candidate.url}: {exc}")
                continue

            content = resp.content
            if len(content) < 2048:
                continue  # probablemente un placeholder/ícono, no una foto de producto

            content_hash = hashlib.sha256(content).hexdigest()
            if content_hash in known_hashes:
                logger.debug(f"Imagen duplicada descartada: {candidate.url}")
                continue

            candidate = refine_score_with_bytes(candidate, content)
            if candidate.score < settings.min_acceptable_score:
                logger.debug(f"Descarta candidato con score {candidate.score}: {candidate.url}")
                continue

            ext = _guess_extension(candidate.url, resp.headers.get("content-type"))
            filename = f"{slugify(product.nombre_normalizado or product.nombre_original)}{ext}"
            dest = settings.images_dir / filename
            dest.write_bytes(content)

            known_hashes.add(content_hash)
            _save_hashes(known_hashes)

            logger.success(
                f"Imagen guardada: {dest.name} (score={candidate.score}, fuente={candidate.source_domain})"
            )
            return DownloadedImage(
                product_key=product.key,
                local_path=str(dest),
                source_url=candidate.url,
                width=candidate.width or 0,
                height=candidate.height or 0,
                score=candidate.score,
            )

        return None
    finally:
        if own_client:
            client.close()
