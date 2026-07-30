"""Módulo 5 — Buscador inteligente.

Construye consultas escalonadas (fabricante -> distribuidor -> genérica -> site:)
y las ejecuta contra un proveedor de búsqueda de imágenes. Por defecto usa
DuckDuckGo (sin API key, vía librería `ddgs`); si hay credenciales de Google
Custom Search en el entorno, se puede añadir como proveedor adicional.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

from loguru import logger

from .config import settings
from .database import Database
from .models import ImageCandidate, Product


class SearchProvider(ABC):
    @abstractmethod
    def search_images(self, query: str, max_results: int) -> list[ImageCandidate]:
        ...


class DuckDuckGoProvider(SearchProvider):
    def search_images(self, query: str, max_results: int) -> list[ImageCandidate]:
        try:
            from ddgs import DDGS
        except ImportError:
            logger.warning("Paquete 'ddgs' no instalado; instala requirements.txt")
            return []

        candidates: list[ImageCandidate] = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.images(query, max_results=max_results):
                    url = r.get("image") or ""
                    if not url:
                        continue
                    candidates.append(
                        ImageCandidate(
                            url=url,
                            source_url=r.get("url", ""),
                            source_domain=urlparse(r.get("url", "")).netloc,
                            query_used=query,
                            width=r.get("width"),
                            height=r.get("height"),
                        )
                    )
        except Exception as exc:  # búsquedas externas pueden fallar por rate-limit, red, etc.
            logger.warning(f"Búsqueda DuckDuckGo falló para '{query}': {exc}")
        return candidates


class DomainPriorityRanker:
    def __init__(self, domains_path: Path | None = None) -> None:
        path = domains_path or (settings.config_dir / "dominios_prioridad.json")
        self._domains: dict[str, list[str]] = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        )

    def tier_for(self, domain: str) -> int:
        domain = (domain or "").lower()
        if any(d in domain for d in self._domains.get("fabricantes", [])):
            return 1
        if any(d in domain for d in self._domains.get("distribuidores_autorizados", [])):
            return 2
        if any(d in domain for d in self._domains.get("marketplace_agricola", [])):
            return 3
        if any(d in domain for d in self._domains.get("tienda_online", [])):
            return 4
        return 5


class SearchEngine:
    def __init__(self, provider: SearchProvider | None = None, db: Database | None = None) -> None:
        self.provider = provider or DuckDuckGoProvider()
        self.domain_ranker = DomainPriorityRanker()
        self.db = db

    def build_queries(self, product: Product) -> list[str]:
        """Módulo 5 — genera consultas en orden de prioridad, con fallback progresivo."""
        name = product.nombre_normalizado or product.nombre_original
        marca = product.marca
        queries: list[str] = []

        if marca and not name.upper().startswith(marca.upper()):
            queries.append(f"{marca} {name}")
        queries.append(name)
        queries.append(f"{name} Chile")
        queries.append(f"{name} distributor")
        if marca:
            manufacturer_domain_hint = marca.lower().replace(" ", "")
            queries.append(f"site:{manufacturer_domain_hint}.cl {name}")
            queries.append(f"site:{manufacturer_domain_hint}.com {name}")

        # Elimina duplicados preservando orden.
        seen: set[str] = set()
        ordered = []
        for q in queries:
            if q and q not in seen:
                seen.add(q)
                ordered.append(q)
        return ordered

    def search(self, query: str, max_results: int | None = None) -> list[ImageCandidate]:
        max_results = max_results or settings.max_search_results_per_query

        if self.db is not None:
            cached = self.db.get_cached_search(query)
            if cached:
                logger.debug(f"Cache hit para consulta: {query}")
                items = json.loads(cached)
                return [ImageCandidate(**item) for item in items]

        results = self.provider.search_images(query, max_results)
        for candidate in results:
            candidate.priority_tier = self.domain_ranker.tier_for(candidate.source_domain)

        if self.db is not None:
            self.db.cache_search(query, json.dumps([r.model_dump() for r in results], default=str))

        return results

    def search_product(self, product: Product) -> list[ImageCandidate]:
        """Módulo 5 + 11 — recorre las consultas en cascada hasta obtener resultados."""
        all_candidates: list[ImageCandidate] = []
        for query in self.build_queries(product):
            results = self.search(query)
            if results:
                all_candidates.extend(results)
                logger.info(f"'{query}' -> {len(results)} resultados")
                break
            logger.debug(f"Sin resultados para '{query}', probando siguiente consulta")
        return all_candidates
