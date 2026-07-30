"""Módulo 4 — Clasificador de categoría por palabras clave (config/categorias.json)."""

from __future__ import annotations

import json
from pathlib import Path

from .config import settings

DEFAULT_CATEGORY = "Otros"


class Classifier:
    def __init__(self, categories_path: Path | None = None) -> None:
        self.categories_path = categories_path or settings.categories_path
        self._categories: dict[str, list[str]] = self._load()

    def _load(self) -> dict[str, list[str]]:
        if self.categories_path.exists():
            return json.loads(self.categories_path.read_text(encoding="utf-8"))
        return {DEFAULT_CATEGORY: []}

    def classify(self, product_name: str, brand: str | None = None) -> str:
        if not product_name:
            return DEFAULT_CATEGORY
        haystack = product_name.upper()
        best_category = DEFAULT_CATEGORY
        best_hits = 0
        for category, keywords in self._categories.items():
            hits = sum(1 for kw in keywords if kw and kw.upper() in haystack)
            if hits > best_hits:
                best_hits = hits
                best_category = category
        return best_category


_default_classifier: Classifier | None = None


def classify_product(product_name: str, brand: str | None = None) -> str:
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = Classifier()
    return _default_classifier.classify(product_name, brand)
