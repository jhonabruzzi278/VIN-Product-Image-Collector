"""Orquestador del flujo completo (Módulos 1-12).

Leer Excel -> Normalizar -> Detectar marca -> Clasificar -> Buscar imágenes ->
Evaluar/rankear -> Descargar (con deduplicación) -> Optimizar -> Verificar con IA ->
Guardar en base de datos -> Reintentar si falla -> Generar reporte.
"""

from __future__ import annotations

from loguru import logger

from .brand_detector import detect_brand
from .classifier import classify_product
from .config import settings
from .database import Database
from .downloader import download_best_image
from .importer import import_products
from .models import CollectionReport, Product, ProductResult, ProductStatus
from .normalizer import normalize_name
from .optimizer import optimize_image
from .ranking import rank_candidates
from .retry import retry_variants
from .search_engine import SearchEngine
from .verifier import get_verifier


def _enrich(product: Product) -> Product:
    product.nombre_normalizado = normalize_name(product.nombre_original)
    if not product.marca:
        marca, _fabricante = detect_brand(product.nombre_normalizado)
        product.marca = marca
    if not product.categoria:
        product.categoria = classify_product(product.nombre_normalizado, product.marca)
    return product


def process_product(product: Product, db: Database, engine: SearchEngine, verifier) -> ProductResult:
    product = _enrich(product)
    db.upsert_product(product)

    result = ProductResult(product=product)

    if db.has_image(product.key):
        logger.debug(f"Ya existe imagen para '{product.key}', se omite")
        product.status = ProductStatus.FOUND
        db.upsert_product(product)
        result.notes = "ya existente en catálogo"
        return result

    candidates = engine.search_product(product)
    result.attempts.append(f"búsqueda inicial: {len(candidates)} candidatos")

    if not candidates:
        for variant in retry_variants(product):
            candidates = engine.search(variant)
            result.attempts.append(f"reintento '{variant}': {len(candidates)} candidatos")
            if candidates:
                break

    if not candidates:
        product.status = ProductStatus.NOT_FOUND
        db.upsert_product(product)
        result.notes = "sin resultados de búsqueda tras reintentos"
        return result

    ranked = rank_candidates(candidates)
    downloaded = download_best_image(product, ranked)

    if not downloaded:
        product.status = ProductStatus.NOT_FOUND
        db.upsert_product(product)
        result.notes = "candidatos encontrados pero ninguno superó el puntaje mínimo"
        return result

    variants = optimize_image(downloaded.local_path)
    downloaded.variants = variants

    best_candidate = next((c for c in ranked if c.url == downloaded.source_url), ranked[0])
    matches, confidence = verifier.verify(product, downloaded.local_path, best_candidate)
    downloaded.ai_verified = matches
    downloaded.ai_confidence = confidence

    db.save_image(downloaded)
    product.status = ProductStatus.FOUND if matches else ProductStatus.NEEDS_REVIEW
    db.upsert_product(product)

    result.image = downloaded
    result.notes = "verificada por IA" if matches else "requiere revisión manual (baja confianza)"
    return result


def run_pipeline(input_path: str) -> tuple[list[ProductResult], CollectionReport]:
    db = Database()
    engine = SearchEngine(db=db)
    verifier = get_verifier()

    products = import_products(input_path)
    results: list[ProductResult] = []

    for i, product in enumerate(products, start=1):
        logger.info(f"[{i}/{len(products)}] Procesando: {product.nombre_original}")
        try:
            result = process_product(product, db, engine, verifier)
        except Exception as exc:
            logger.exception(f"Error procesando '{product.nombre_original}': {exc}")
            product.status = ProductStatus.NOT_FOUND
            result = ProductResult(product=product, notes=f"error: {exc}")
        results.append(result)

    counts = db.counts()
    report = CollectionReport(
        total=counts["total"], encontrados=counts["encontrados"], pendientes=counts["pendientes"]
    )
    logger.info(
        f"Pipeline finalizado: {report.encontrados}/{report.total} encontrados "
        f"({report.cobertura_pct}% cobertura)"
    )
    return results, report
