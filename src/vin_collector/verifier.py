"""Módulo 9 — IA de verificación: ¿la imagen realmente corresponde al producto?

Por defecto usa un verificador heurístico (sin costo, sin dependencias externas).
Si se define ANTHROPIC_API_KEY, se puede usar AnthropicVisionVerifier para una
verificación real con un modelo de visión.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from loguru import logger

from .config import settings
from .models import ImageCandidate, Product


class ImageVerifier(ABC):
    @abstractmethod
    def verify(self, product: Product, image_path: str | Path, candidate: ImageCandidate) -> tuple[bool, float]:
        """Devuelve (coincide, confianza 0-1)."""


class HeuristicVerifier(ImageVerifier):
    """Compara tokens del nombre/marca del producto contra la URL, dominio y consulta usada."""

    def verify(self, product: Product, image_path: str | Path, candidate: ImageCandidate) -> tuple[bool, float]:
        # La consulta contiene el nombre esperado por definiciÃ³n y no es evidencia
        # de que el resultado realmente corresponda al producto.
        haystack = " ".join(
            [candidate.title, candidate.url, candidate.source_url, candidate.source_domain]
        ).upper()

        ignored = {"PARA", "CON", "DEL", "LOS", "LAS", "UND", "UNIDAD", "LITRO", "SACO", "BIDON"}
        tokens = [
            t for t in (product.nombre_normalizado or product.nombre_original).upper().split()
            if len(t) > 2 and t not in ignored
        ]
        if product.marca:
            tokens.append(product.marca.upper())

        if not tokens:
            return True, 0.5

        hits = sum(1 for t in tokens if t in haystack)
        confidence = min(1.0, hits / max(1, len(tokens)))
        # También favorece candidatos de dominios prioritarios (fabricante/distribuidor).
        if candidate.priority_tier <= 2:
            confidence = min(1.0, confidence + 0.15)

        matches = confidence >= 0.4
        return matches, round(confidence, 2)


class AnthropicVisionVerifier(ImageVerifier):
    """Verificación real con modelo de visión de Anthropic (requiere ANTHROPIC_API_KEY)."""

    def __init__(self) -> None:
        from anthropic import Anthropic  # import diferido: dependencia opcional

        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def verify(self, product: Product, image_path: str | Path, candidate: ImageCandidate) -> tuple[bool, float]:
        import base64

        image_path = Path(image_path)
        media_type = "image/webp" if image_path.suffix == ".webp" else "image/jpeg"
        image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")

        prompt = (
            f"¿Esta imagen corresponde realmente al producto '{product.nombre_original}' "
            f"(marca: {product.marca or 'desconocida'})? Responde solo en formato "
            "'SI|NO|confianza_0_a_100'."
        )

        try:
            response = self._client.messages.create(
                model="claude-sonnet-5",
                max_tokens=20,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            text = response.content[0].text.strip().upper()
            parts = text.split("|")
            matches = parts[0].startswith("SI")
            confidence = float(parts[2]) / 100 if len(parts) > 2 else (0.9 if matches else 0.1)
            return matches, round(confidence, 2)
        except Exception as exc:
            logger.warning(f"Verificación con IA de visión falló, se usa heurística: {exc}")
            return HeuristicVerifier().verify(product, image_path, candidate)


def get_verifier() -> ImageVerifier:
    if settings.anthropic_api_key:
        try:
            return AnthropicVisionVerifier()
        except ImportError:
            logger.debug("anthropic no instalado; usando verificador heurístico")
    return HeuristicVerifier()
