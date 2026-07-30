"""Módulo 2 — Normalizador de nombres de producto.

Combina reglas regex para unidades/formato con similitud difusa (RapidFuzz)
contra un diccionario de nombres canónicos que crece con el uso (cache/normalizer_dictionary.json).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from rapidfuzz import fuzz, process

from .config import settings

UNIT_PATTERNS: list[tuple[re.Pattern, str]] = [
    # "X1 LT", "X 1 LT" -> "1 LT"
    (re.compile(r"\bX\s*(\d+(?:[.,]\d+)?)\s*(LTS?|LITROS?)\b", re.I), r"\1 LT"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(LTS?|LITROS?|L)\b", re.I), r"\1 LT"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(KGS?|KILOS?|KG)\b", re.I), r"\1 KG"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(GRS?|GRAMOS?|G)\b", re.I), r"\1 GR"),
    (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(CCS?|ML|MILILITROS?)\b", re.I), r"\1 CC"),
]

FUZZY_THRESHOLD = 90


class NameNormalizer:
    def __init__(self, dictionary_path: Path | None = None) -> None:
        self.dictionary_path = dictionary_path or (settings.cache_dir / "normalizer_dictionary.json")
        self._canonical_names: list[str] = self._load()

    def _load(self) -> list[str]:
        if self.dictionary_path.exists():
            return json.loads(self.dictionary_path.read_text(encoding="utf-8"))
        return []

    def _save(self) -> None:
        self.dictionary_path.parent.mkdir(parents=True, exist_ok=True)
        self.dictionary_path.write_text(
            json.dumps(sorted(set(self._canonical_names)), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _apply_rules(raw: str) -> str:
        text = raw.upper().strip()
        text = re.sub(r"[.](?!\d)", " ", text)  # puntos que no son decimales -> espacio
        text = re.sub(r"[_/]", " ", text)
        for pattern, repl in UNIT_PATTERNS:
            text = pattern.sub(repl, text)
        text = re.sub(r"\s+", " ", text).strip()
        # Normaliza decimales con coma a punto (ej. "1,8 EC" -> "1.8 EC")
        text = re.sub(r"(\d+),(\d+)", r"\1.\2", text)
        return text

    def normalize(self, raw_name: str, learn: bool = True) -> str:
        if not raw_name:
            return ""
        candidate = self._apply_rules(raw_name)

        if self._canonical_names:
            match = process.extractOne(
                candidate, self._canonical_names, scorer=fuzz.token_sort_ratio
            )
            if match and match[1] >= FUZZY_THRESHOLD:
                return match[0]

        if learn:
            self._canonical_names.append(candidate)
            self._save()
        return candidate


_default_normalizer: NameNormalizer | None = None


def normalize_name(raw_name: str) -> str:
    global _default_normalizer
    if _default_normalizer is None:
        _default_normalizer = NameNormalizer()
    return _default_normalizer.normalize(raw_name)
