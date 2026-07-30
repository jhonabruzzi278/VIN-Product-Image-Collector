"""Módulo 3 — Detector de marca a partir de config/marcas.json."""

from __future__ import annotations

import json
from pathlib import Path

from rapidfuzz import fuzz, process

from .config import settings

FUZZY_THRESHOLD = 85


class BrandDetector:
    def __init__(self, brands_path: Path | None = None) -> None:
        self.brands_path = brands_path or settings.brands_path
        self._brands: dict[str, str] = self._load()

    def _load(self) -> dict[str, str]:
        if self.brands_path.exists():
            return json.loads(self.brands_path.read_text(encoding="utf-8"))
        return {}

    def _save(self) -> None:
        self.brands_path.parent.mkdir(parents=True, exist_ok=True)
        self.brands_path.write_text(
            json.dumps(dict(sorted(self._brands.items())), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def detect(self, product_name: str) -> tuple[str | None, str | None]:
        """Devuelve (marca_producto, fabricante) o (None, None) si no se detecta."""
        if not product_name or not self._brands:
            return None, None

        name_upper = product_name.upper()

        # 1) Coincidencia exacta por substring (más confiable)
        for brand, manufacturer in self._brands.items():
            if brand in name_upper:
                return brand, manufacturer

        # 2) Similitud difusa contra la primera palabra significativa del nombre
        first_token = name_upper.split(" ")[0]
        match = process.extractOne(first_token, self._brands.keys(), scorer=fuzz.ratio)
        if match and match[1] >= FUZZY_THRESHOLD:
            brand = match[0]
            return brand, self._brands[brand]

        return None, None

    def learn(self, brand: str, manufacturer: str) -> None:
        """Registra una nueva marca -> fabricante para que la base crezca con el tiempo."""
        self._brands[brand.upper().strip()] = manufacturer.upper().strip()
        self._save()


_default_detector: BrandDetector | None = None


def detect_brand(product_name: str) -> tuple[str | None, str | None]:
    global _default_detector
    if _default_detector is None:
        _default_detector = BrandDetector()
    return _default_detector.detect(product_name)
