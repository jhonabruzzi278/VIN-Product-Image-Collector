"""Módulo 1 — Importador: lee Excel, CSV o TXT y produce una lista de Product."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from .models import Product

# Mapea encabezados habituales (en cualquier idioma/mayúscula) a nuestros campos.
COLUMN_ALIASES: dict[str, str] = {
    "sku": "sku",
    "codigo": "sku",
    "código": "sku",
    "cod": "sku",
    "nombre": "nombre_original",
    "producto": "nombre_original",
    "descripcion": "nombre_original",
    "descripción": "nombre_original",
    "marca": "marca",
    "categoria": "categoria",
    "categoría": "categoria",
    "ean": "ean",
    "ean13": "ean",
    "codigo_barras": "ean",
    "proveedor": "proveedor",
    "supplier": "proveedor",
}


def _normalize_headers(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for col in columns:
        key = str(col).strip().lower()
        if key in COLUMN_ALIASES:
            mapping[col] = COLUMN_ALIASES[key]
    return mapping


def _read_any(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str, sep=None, engine="python")
    if suffix == ".txt":
        # Asume texto delimitado por tabulaciones; si no, una columna "nombre" por línea.
        try:
            return pd.read_csv(path, dtype=str, sep="\t")
        except Exception:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            return pd.DataFrame({"nombre": [line.strip() for line in lines if line.strip()]})
    raise ValueError(f"Formato no soportado: {suffix}")


def _clean(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def import_products(path: str | Path) -> list[Product]:
    """Lee un archivo de productos y devuelve una lista de Product normalizados en campos."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {path}")

    df = _read_any(path)
    df = df.rename(columns=_normalize_headers(list(df.columns)))

    products: list[Product] = []
    for _, row in df.iterrows():
        data = row.to_dict()
        nombre = _clean(data.get("nombre_original"))
        sku = _clean(data.get("sku"))
        if not nombre and not sku:
            continue
        product = Product(
            sku=sku or None,
            nombre_original=nombre,
            marca=_clean(data.get("marca")) or None,
            categoria=_clean(data.get("categoria")) or None,
            ean=_clean(data.get("ean")) or None,
            proveedor=_clean(data.get("proveedor")) or None,
        )
        products.append(product)

    logger.info(f"Importados {len(products)} productos desde {path.name}")
    return products
