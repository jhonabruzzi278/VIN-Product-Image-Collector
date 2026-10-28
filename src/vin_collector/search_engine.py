"""Módulo 5 — Buscador inteligente.

Construye consultas escalonadas (fabricante -> distribuidor -> genérica -> site:)
y las ejecuta contra un proveedor de búsqueda de imágenes. Por defecto usa
DuckDuckGo (sin API key, vía librería `ddgs`); si hay credenciales de Google
Custom Search en el entorno, se puede añadir como proveedor adicional.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
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
                            title=r.get("title", ""),
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


class BingImageProvider(SearchProvider):
    """Fallback sin API para cuando DuckDuckGo limita las consultas masivas."""

    def search_images(self, query: str, max_results: int) -> list[ImageCandidate]:
        candidates: list[ImageCandidate] = []
        try:
            response = httpx.get(
                "https://www.bing.com/images/search",
                params={"q": query, "form": "HDRSC2", "first": 1},
                headers={"User-Agent": settings.request_user_agent},
                timeout=settings.http_timeout_seconds,
                follow_redirects=True,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            for item in soup.select("a.iusc"):
                raw = item.get("m")
                if not raw:
                    continue
                data = json.loads(raw)
                url = data.get("murl") or ""
                if not url:
                    continue
                source_url = data.get("purl") or ""
                candidates.append(
                    ImageCandidate(
                        url=url,
                        title=data.get("t") or item.get("aria-label") or "",
                        source_url=source_url,
                        source_domain=urlparse(source_url).netloc,
                        query_used=query,
                        width=data.get("md5") and data.get("w"),
                        height=data.get("md5") and data.get("h"),
                    )
                )
                if len(candidates) >= max_results:
                    break
        except Exception as exc:
            logger.warning(f"Búsqueda Bing falló para '{query}': {exc}")
        return candidates


class FallbackSearchProvider(SearchProvider):
    def __init__(self, providers: list[SearchProvider]) -> None:
        self.providers = providers

    def search_images(self, query: str, max_results: int) -> list[ImageCandidate]:
        for provider in self.providers:
            results = provider.search_images(query, max_results)
            if results:
                return results
        return []


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
        self.provider = provider or FallbackSearchProvider([DuckDuckGoProvider(), BingImageProvider()])
        self.domain_ranker = DomainPriorityRanker()
        self.db = db

    def build_queries(self, product: Product) -> list[str]:
        """Módulo 5 — genera consultas en orden de prioridad, con fallback progresivo."""
        name = product.nombre_normalizado or product.nombre_original
        marca = product.marca
        queries: list[str] = []

        # Los SKU de Victorinox usados por Agro Farías derivan del número de
        # artículo oficial (p. ej. NAV9415DS23 -> 0.9415.DS23). Buscar primero
        # ese identificador reduce drásticamente confusiones entre variantes.
        sku = (product.sku or "").upper().replace(" ", "")
        if sku.startswith("NAV"):
            compact = sku[3:]
            match = re.fullmatch(r"(\d{4})([A-Z].*|\d)", compact)
            if match:
                official_code = f"0.{match.group(1)}.{match.group(2)}"
                queries.append(f'Victorinox "{official_code}"')

        if product.sku:
            queries.append(f'"{product.sku}" {marca or ""} {name}'.strip())

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
