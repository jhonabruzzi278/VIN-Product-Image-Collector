"""Módulo 6 — Ranking de candidatos de imagen.

Puntúa cada ImageCandidate en una escala 0-100 combinando señales disponibles
antes de descargar (resolución, prioridad de dominio, coincidencia de consulta)
y, cuando se dispone de los bytes de la imagen, señales visuales (fondo blanco,
producto centrado, ausencia de marca de agua aproximada).
"""

from __future__ import annotations

import io
import re
import unicodedata

from loguru import logger

from .models import ImageCandidate, Product

WEIGHTS = {
    "relevancia": 35,
    "resolucion": 20,
    "prioridad_dominio": 20,
    "fondo_blanco": 10,
    "centrado": 10,
    "sin_marca_agua": 5,
}

_GENERIC_TOKENS = {
    "para", "por", "con", "sin", "del", "las", "los", "una", "uno", "producto",
    "agricola", "agricultura", "chile", "comprar", "venta", "tienda", "imagen", "foto",
    "litro", "litros", "unidad", "unidades", "saco", "bidon", "tambor",
}


def _tokens(value: str) -> set[str]:
    value = unicodedata.normalize("NFD", value or "")
    value = "".join(char for char in value if unicodedata.category(char) != "Mn").lower()
    return {
        token for token in re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", value)
        if len(token) > 2 and token not in _GENERIC_TOKENS
    }


def _score_relevance(candidate: ImageCandidate, product: Product | None) -> float:
    if product is None:
        return 0.5
    expected = _tokens(" ".join(filter(None, [product.nombre_normalizado, product.marca or "", product.sku or ""])))
    evidence = _tokens(" ".join([candidate.title, candidate.source_url, candidate.url]))
    if not expected or not evidence:
        return 0.0
    return len(expected & evidence) / len(expected)


def _score_resolution(width: int | None, height: int | None) -> float:
    if not width or not height:
        return 0.4  # desconocido: puntaje neutro-bajo
    min_side = min(width, height)
    if min_side >= 1200:
        return 1.0
    if min_side >= 800:
        return 0.85
    if min_side >= 400:
        return 0.6
    if min_side >= 200:
        return 0.35
    return 0.1


def _score_domain_priority(tier: int) -> float:
    # tier 1 (fabricante) -> 1.0 ... tier 5 (google images genérico) -> 0.2
    return max(0.2, 1.2 - tier * 0.2)


def score_candidate(candidate: ImageCandidate, product: Product | None = None) -> ImageCandidate:
    """Puntuación basada solo en metadatos (rápida, sin descargar la imagen)."""
    res_score = _score_resolution(candidate.width, candidate.height)
    dom_score = _score_domain_priority(candidate.priority_tier)

    breakdown = {
        "relevancia": round(_score_relevance(candidate, product) * WEIGHTS["relevancia"], 1),
        "resolucion": round(res_score * WEIGHTS["resolucion"], 1),
        "prioridad_dominio": round(dom_score * WEIGHTS["prioridad_dominio"], 1),
        # Sin bytes de imagen aún: valores neutros hasta refinar tras la descarga.
        "fondo_blanco": round(0.5 * WEIGHTS["fondo_blanco"], 1),
        "centrado": round(0.5 * WEIGHTS["centrado"], 1),
        "sin_marca_agua": round(0.7 * WEIGHTS["sin_marca_agua"], 1),
    }
    candidate.score_breakdown = breakdown
    candidate.score = round(sum(breakdown.values()), 1)
    return candidate


def rank_candidates(candidates: list[ImageCandidate], product: Product | None = None) -> list[ImageCandidate]:
    scored = [score_candidate(c, product) for c in candidates]
    return sorted(scored, key=lambda c: c.score, reverse=True)


def refine_score_with_bytes(candidate: ImageCandidate, image_bytes: bytes) -> ImageCandidate:
    """Refina el puntaje con análisis visual real (Pillow) tras descargar la imagen."""
    try:
        from PIL import Image
    except ImportError:
        return candidate

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        logger.debug(f"No se pudo abrir la imagen para refinar puntaje: {exc}")
        return candidate

    width, height = img.size
    candidate.width, candidate.height = width, height

    white_bg_score = _estimate_white_background(img)
    centered_score = _estimate_centered_subject(img)
    watermark_score = _estimate_no_watermark(img)

    breakdown = dict(candidate.score_breakdown)
    breakdown.setdefault("relevancia", round(0.5 * WEIGHTS["relevancia"], 1))
    breakdown["resolucion"] = round(_score_resolution(width, height) * WEIGHTS["resolucion"], 1)
    breakdown["fondo_blanco"] = round(white_bg_score * WEIGHTS["fondo_blanco"], 1)
    breakdown["centrado"] = round(centered_score * WEIGHTS["centrado"], 1)
    breakdown["sin_marca_agua"] = round(watermark_score * WEIGHTS["sin_marca_agua"], 1)

    candidate.score_breakdown = breakdown
    candidate.score = round(sum(breakdown.values()), 1)
    candidate.has_watermark_guess = watermark_score < 0.5
    return candidate


def _estimate_white_background(img) -> float:
    """Muestrea las esquinas y bordes: si son casi blancos, asumimos fondo blanco."""
    w, h = img.size
    sample_points = [
        (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
        (w // 2, 0), (0, h // 2), (w - 1, h // 2), (w // 2, h - 1),
    ]
    near_white = 0
    for x, y in sample_points:
        r, g, b = img.getpixel((x, y))
        if r > 235 and g > 235 and b > 235:
            near_white += 1
    return near_white / len(sample_points)


def _estimate_centered_subject(img) -> float:
    """Heurística simple: compara el brillo del centro vs el promedio del borde.

    Un producto centrado sobre fondo claro suele producir una región central
    más oscura/variada que los bordes (que tienden a ser fondo uniforme).
    """
    w, h = img.size
    if w < 10 or h < 10:
        return 0.5
    gray = img.convert("L")
    cx0, cy0, cx1, cy1 = w // 3, h // 3, (2 * w) // 3, (2 * h) // 3
    center = gray.crop((cx0, cy0, cx1, cy1))
    center_pixels = list(center.getdata())
    center_std = _stddev(center_pixels)
    border_pixels = [
        gray.getpixel((0, 0)), gray.getpixel((w - 1, 0)),
        gray.getpixel((0, h - 1)), gray.getpixel((w - 1, h - 1)),
    ]
    border_std = _stddev(border_pixels) or 1.0
    ratio = min(center_std / max(border_std, 5.0), 3.0) / 3.0
    return max(0.2, min(1.0, ratio + 0.3))


def _estimate_no_watermark(img) -> float:
    """Heurística débil: mucho texto/ruido de alta frecuencia en los bordes sugiere marca de agua."""
    w, h = img.size
    gray = img.convert("L")
    strip_height = max(1, h // 10)
    bottom_strip = gray.crop((0, h - strip_height, w, h))
    pixels = list(bottom_strip.getdata())
    std = _stddev(pixels)
    # Mucha variación en la franja inferior (típico de texto de marca de agua) -> puntaje menor.
    if std > 60:
        return 0.3
    if std > 35:
        return 0.6
    return 0.9


def _stddev(values: list[int]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5
