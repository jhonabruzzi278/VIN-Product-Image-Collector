"""Módulo 10 — Base de datos (SQLite) de catálogo y caché de búsquedas."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    key TEXT PRIMARY KEY,
    sku TEXT,
    nombre_original TEXT,
    nombre_normalizado TEXT,
    marca TEXT,
    categoria TEXT,
    ean TEXT,
    proveedor TEXT,
    status TEXT NOT NULL DEFAULT 'pendiente',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_key TEXT NOT NULL REFERENCES products(key),
    local_path TEXT NOT NULL,
    source_url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    score REAL,
    ai_verified INTEGER,
    ai_confidence REAL,
    variants_json TEXT
);

CREATE TABLE IF NOT EXISTS search_cache (
    query TEXT PRIMARY KEY,
    results_json TEXT NOT NULL,
    cached_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_images_product_key ON images(product_key);
"""


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert_product(self, product) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO products (key, sku, nombre_original, nombre_normalizado,
                                       marca, categoria, ean, proveedor, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    sku=excluded.sku,
                    nombre_original=excluded.nombre_original,
                    nombre_normalizado=excluded.nombre_normalizado,
                    marca=excluded.marca,
                    categoria=excluded.categoria,
                    ean=excluded.ean,
                    proveedor=excluded.proveedor,
                    status=excluded.status,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    product.key,
                    product.sku,
                    product.nombre_original,
                    product.nombre_normalizado,
                    product.marca,
                    product.categoria,
                    product.ean,
                    product.proveedor,
                    product.status.value,
                ),
            )

    def get_product(self, key: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM products WHERE key = ?", (key,)).fetchone()

    def has_image(self, product_key: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM images WHERE product_key = ? LIMIT 1", (product_key,)
            ).fetchone()
            return row is not None

    def save_image(self, image) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO images (product_key, local_path, source_url, fetched_at,
                                     width, height, score, ai_verified, ai_confidence, variants_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image.product_key,
                    image.local_path,
                    image.source_url,
                    image.fetched_at.isoformat(),
                    image.width,
                    image.height,
                    image.score,
                    None if image.ai_verified is None else int(image.ai_verified),
                    image.ai_confidence,
                    json.dumps(image.variants, ensure_ascii=False),
                ),
            )

    def cache_search(self, query: str, results_json: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO search_cache (query, results_json) VALUES (?, ?)
                ON CONFLICT(query) DO UPDATE SET results_json=excluded.results_json,
                    cached_at=CURRENT_TIMESTAMP
                """,
                (query, results_json),
            )

    def get_cached_search(self, query: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT results_json FROM search_cache WHERE query = ?", (query,)
            ).fetchone()
            return row["results_json"] if row else None

    def counts(self) -> dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
            encontrados = conn.execute(
                "SELECT COUNT(*) c FROM products WHERE status = 'encontrado'"
            ).fetchone()["c"]
            pendientes = total - encontrados
            return {"total": total, "encontrados": encontrados, "pendientes": pendientes}

    def all_products_with_images(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT p.*, i.local_path, i.source_url, i.width, i.height, i.score,
                       i.ai_verified, i.ai_confidence, i.variants_json
                FROM products p
                LEFT JOIN images i ON i.product_key = p.key
                    AND i.id = (SELECT MAX(id) FROM images WHERE product_key = p.key)
                ORDER BY p.nombre_normalizado
                """
            ).fetchall()
