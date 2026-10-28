"""Modelos de datos compartidos entre módulos (Pydantic)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ProductStatus(StrEnum):
    PENDING = "pendiente"
    FOUND = "encontrado"
    NOT_FOUND = "no_encontrado"
    NEEDS_REVIEW = "requiere_revision"


class Product(BaseModel):
    sku: str | None = None
    nombre_original: str = ""
    nombre_normalizado: str = ""
    marca: str | None = None
    categoria: str | None = None
    ean: str | None = None
    proveedor: str | None = None
    status: ProductStatus = ProductStatus.PENDING

    @property
    def key(self) -> str:
        return self.sku or self.ean or self.nombre_normalizado or self.nombre_original


class ImageCandidate(BaseModel):
    url: str
    title: str = ""
    source_url: str = ""
    source_domain: str = ""
    query_used: str = ""
    width: int | None = None
    height: int | None = None
    score: float = 0.0
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    priority_tier: int = 5  # 1=fabricante ... 5=google images
    has_watermark_guess: bool = False


class DownloadedImage(BaseModel):
    product_key: str
    local_path: str
    source_url: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    width: int
    height: int
    score: float
    ai_verified: bool | None = None
    ai_confidence: float | None = None
    variants: dict[str, str] = Field(default_factory=dict)  # nombre -> ruta


class ProductResult(BaseModel):
    product: Product
    image: DownloadedImage | None = None
    attempts: list[str] = Field(default_factory=list)
    notes: str = ""


class CollectionReport(BaseModel):
    total: int
    encontrados: int
    pendientes: int
    generado_en: datetime = Field(default_factory=datetime.utcnow)

    @property
    def cobertura_pct(self) -> float:
        return round((self.encontrados / self.total) * 100, 1) if self.total else 0.0
