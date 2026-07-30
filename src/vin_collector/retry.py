"""Módulo 11 — Reintentos: variantes de consulta progresivamente más simples."""

from __future__ import annotations

from .models import Product


def retry_variants(product: Product) -> list[str]:
    """Genera variantes de búsqueda cada vez más genéricas para reintentar tras un fallo."""
    name = product.nombre_normalizado or product.nombre_original
    first_word = name.split(" ")[0] if name else ""

    variants: list[str] = []
    if name:
        variants.append(name)
    if first_word:
        variants.append(first_word)
        variants.append(f"{first_word} EC")
        if product.marca:
            variants.append(f"{first_word} {product.marca}")
    if product.sku:
        variants.append(product.sku)
    if product.ean:
        variants.append(product.ean)

    seen: set[str] = set()
    ordered = []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            ordered.append(v)
    return ordered
