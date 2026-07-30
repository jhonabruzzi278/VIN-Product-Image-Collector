# Domain Model (DDD)

Extraído directamente de `src/vin_collector/models.py` y `database.py` (código real, no
un modelo aspiracional escrito aparte).

## Bounded Context: Catálogo de Productos e Imágenes

Un único bounded context — el proyecto no separa contextos (ej. no hay un contexto
"Pricing" o "Inventario" distinto). Todo el dominio gira en torno a: producto → imagen
asociada → resultado del procesamiento.

### Aggregate Root: `Product`

```python
class Product(BaseModel):
    sku, nombre_original, nombre_normalizado, marca, categoria, ean, proveedor, status
    @property
    def key(self) -> str  # sku or ean or nombre_normalizado or nombre_original
```

- **Identidad de negocio**: no es un campo único fijo — `key` resuelve identidad con fallback
  (SKU → EAN → nombre normalizado → nombre original). Esto es una decisión de diseño real
  y pragmática (listados de proveedores no siempre tienen SKU/EAN), pero también un **riesgo
  de dominio**: dos productos con el mismo nombre normalizado y sin SKU/EAN colisionan en
  la misma fila de la tabla `products` (mismo `key`). No hay salvaguarda contra esto en el
  código actual.
- **status**: `ProductStatus` (enum) — `pendiente | encontrado | no_encontrado | requiere_revision`.
  Es el ciclo de vida del aggregate.

### Value Objects

- **`ProductStatus`** (`StrEnum`) — inmutable, sin identidad propia, define un conjunto
  cerrado de estados válidos.
- **`ImageCandidate`** — resultado efímero de búsqueda (url, dominio, score, tier de
  prioridad). No se persiste como entidad propia; vive solo durante el pipeline en memoria
  y (serializado) en la caché de búsquedas (`search_cache` en SQLite).
- **`DownloadedImage`** — snapshot inmutable de una descarga: ruta local, URL fuente, fecha,
  dimensiones, score, veredicto de verificación IA, variantes generadas. Se persiste en la
  tabla `images`, pero conceptualmente es un Value Object asociado al Product (no tiene
  ciclo de vida propio independiente — vive y muere con la evidencia de esa descarga).

### Entidad relacionada (secundaria): `DownloadedImage` en la base de datos

Aunque modelada como Pydantic "value object" en `models.py`, en `database.py` la tabla
`images` tiene su propio `id INTEGER PRIMARY KEY AUTOINCREMENT` y guarda **histórico**
(`all_products_with_images()` usa `MAX(id)` para tomar la más reciente por producto) — en
la práctica se comporta como una **entidad con identidad técnica propia** relacionada 1-a-N
con `Product` vía `product_key`. Vale la pena decidir explícitamente en el próximo ciclo de
diseño si `images` debe modelarse como historial versionado (como está hoy, correctamente)
o si se espera solo 1 imagen vigente por producto (en cuyo caso el histórico es ruido).

### Repository

- **`Database`** (`database.py`) — implementa el patrón Repository de facto sobre SQLite:
  `upsert_product`, `get_product`, `has_image`, `save_image`, `cache_search`,
  `get_cached_search`, `counts`, `all_products_with_images`. No hay una interfaz abstracta
  `Repository` separada de la implementación SQLite — si en el futuro se necesita
  PostgreSQL (como sugería el brief original), habría que extraer una interfaz primero.

### Domain Events

**No implementados.** El pipeline es síncrono e imperativo (`pipeline.py::process_product`
llama directamente a cada módulo en secuencia). No hay pub/sub, cola de eventos, ni
`DomainEvent` explícito (ej. `ImagenEncontrada`, `ProductoRequiereRevision`). Es coherente
con el tamaño actual del sistema (un solo proceso CLI), pero es la primera pieza a añadir
si el proyecto evoluciona a procesamiento asíncrono/distribuido o a notificaciones
(ej. alertar cuando un producto queda en `requiere_revision`).

### Otros modelos (no-aggregate, DTOs de aplicación)

- **`ProductResult`** — DTO de salida del pipeline por producto (producto + imagen +
  intentos + notas). No se persiste; es para reporting/depuración en memoria.
- **`CollectionReport`** — DTO de resumen (total/encontrados/pendientes + `cobertura_pct`
  calculada). Consumido por `report.py` y por el CLI.
