"""Módulo 1 — Importador: lee Excel, CSV o TXT y produce una lista de Product."""

from __future__ import annotations

import csv
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
        # "utf-8-sig" ya retira el BOM al leer, pero se limpia aquí también por si
        # el DataFrame llega de otra fuente (ej. un futuro proveedor) que no lo haga.
        key = str(col).strip().lstrip("﻿").lower()
        if key in COLUMN_ALIASES:
            mapping[col] = COLUMN_ALIASES[key]
    return mapping


_DELIMITER_CANDIDATES = (",", ";", "\t", "|")


def _detect_delimiter(first_line: str) -> str | None:
    """Elige el delimitador más frecuente entre los candidatos habituales.

    Devuelve None si ninguno aparece en la línea — en ese caso el archivo es de
    una sola columna y no debe intentarse dividir en absoluto.
    """
    counts = {d: first_line.count(d) for d in _DELIMITER_CANDIDATES}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else None


def _read_single_field_rows(path: Path) -> list[str]:
    """Lee cada línea como un único campo CSV (respeta comillas envolventes).

    Aunque no haya un delimitador real entre columnas, una línea puede venir
    entrecomillada por el exportador original (ej. Excel entrecomilla cualquier
    campo que contenga una coma, incluso siendo la única columna). Usar
    `csv.reader` en vez de `line.strip()` evita dejar las comillas literales
    pegadas al nombre del producto (lo que degradaría la calidad de búsqueda).
    """
    with path.open(encoding="utf-8-sig", errors="ignore", newline="") as f:
        rows = [row[0].strip() for row in csv.reader(f) if row and row[0].strip()]
    return rows


def _read_single_column_csv(path: Path) -> pd.DataFrame:
    """CSV de una sola columna sin delimitador (ej. solo nombres de producto).

    La primera línea se trata como encabezado — por convención CSV — para que
    pase por `_normalize_headers` (ej. "PRODUCTO" -> nombre_original).
    """
    rows = _read_single_field_rows(path)
    if not rows:
        return pd.DataFrame()
    header, *data = rows
    return pd.DataFrame({header: data})


def _read_single_column_txt(path: Path) -> pd.DataFrame:
    """TXT plano, una línea por producto, sin encabezado esperado."""
    return pd.DataFrame({"nombre": _read_single_field_rows(path)})


def _read_any(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    if suffix in (".csv", ".txt"):
        # "utf-8-sig" retira el BOM que agregan Excel/otras herramientas al exportar
        # como "CSV UTF-8" — sin esto, el encabezado queda como "﻿PRODUCTO" y no
        # matchea contra COLUMN_ALIASES, descartando todas las filas silenciosamente.
        with path.open(encoding="utf-8-sig", errors="ignore") as f:
            first_line = f.readline()

        # No usar sep=None (auto-detección de pandas/csv.Sniffer): en archivos de
        # una sola columna sin delimitador real (ej. solo "PRODUCTO" como encabezado),
        # el Sniffer puede "inventar" un delimitador a partir de letras repetidas
        # (ej. partió "PRODUCTO" en "PR"/"DUCT" usando la "O" como separador),
        # perdiendo la columna de nombre por completo y dejando 0 productos importados.
        delimiter = _detect_delimiter(first_line)
        if delimiter is None:
            return _read_single_column_csv(path) if suffix == ".csv" else _read_single_column_txt(path)
        return pd.read_csv(path, dtype=str, sep=delimiter, engine="python", encoding="utf-8-sig")
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
