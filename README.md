# VIN Product Image Collector

Motor de enriquecimiento de catálogos: toma un listado de productos (Excel/CSV/TXT)
y devuelve un catálogo con imágenes verificadas, optimizadas y listas para e-commerce.

## Flujo

```
Leer Excel/CSV/TXT → Normalizar nombres → Detectar marca → Clasificar categoría
→ Buscar imágenes → Rankear candidatos → Descargar (con deduplicación)
→ Optimizar (WebP + miniaturas) → Verificar con IA → Guardar en SQLite → Reporte
```

Cada módulo del diseño original vive en su propio archivo bajo `src/vin_collector/`:

| Módulo | Archivo |
|---|---|
| 1. Importador | `importer.py` |
| 2. Normalizador | `normalizer.py` |
| 3. Detector de marca | `brand_detector.py` |
| 4. Clasificador | `classifier.py` |
| 5. Buscador inteligente | `search_engine.py` |
| 6. Ranking | `ranking.py` |
| 7. Descarga (+ deduplicación) | `downloader.py` |
| 8. Optimizador | `optimizer.py` |
| 9. IA de verificación | `verifier.py` |
| 10. Base de datos | `database.py` |
| 11. Reintentos | `retry.py` |
| 12. Reporte | `report.py` |
| Orquestador | `pipeline.py` |
| CLI | `cli.py` |

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Copia `.env.example` a `.env` si quieres activar proveedores opcionales:
- `ANTHROPIC_API_KEY` → verificación de imágenes con IA de visión real (Módulo 9).
  Sin esta clave se usa un verificador heurístico local (gratis, sin dependencias externas).
- `GOOGLE_CSE_API_KEY` / `GOOGLE_CSE_CX` → reservado para añadir Google Custom Search
  como proveedor de búsqueda adicional (por defecto se usa DuckDuckGo, sin API key).

## Uso

```bash
# Coloca tu listado en input/productos.xlsx (o .csv / .txt)
vin-collector run input/productos.xlsx

# Regenerar solo el reporte (catalogo.csv + reporte.html) desde la base de datos
vin-collector report

# Ver cobertura actual
vin-collector status
```

Salidas en `output/`:
- `images/` — imagen original + versión `.webp` por producto.
- `thumbnails/` — miniaturas en 200/400/800/1200 px.
- `catalogo.csv` — catálogo tabular.
- `reporte.html` — reporte visual con miniaturas, estado, score y fuente.

El progreso se guarda en `database/catalog.db` (SQLite), así que volver a correr
`run` sobre el mismo listado no vuelve a descargar productos ya resueltos.

## Campos de entrada aceptados

`SKU`, `Nombre`, `Marca`, `Categoría`, `EAN`, `Proveedor` (encabezados flexibles,
en español o inglés). Solo `Nombre` o `SKU` son obligatorios — el resto se infiere:
marca vía `config/marcas.json`, categoría vía `config/categorias.json`.

Estos dos JSON son bases de conocimiento vivas: agrega marcas o categorías nuevas
y el sistema las usará en la próxima corrida.

## Pruebas

```bash
pytest -q
```

## Próximos pasos sugeridos (evolución hacia motor de enriquecimiento completo)

El diseño deja espacio para crecer más allá de imágenes: descripciones, specs
técnicas, fichas PDF/MSDS, texto alt para SEO y exportación a WooCommerce/Shopify/
Prestashop. Cada uno encajaría como un módulo adicional que consume el mismo
`Product`/`DownloadedImage` y escribe en la misma base SQLite.

## 📋 Documentación del Proyecto (AI-DLC)

Este proyecto sigue la metodología AI-DLC. Estado actual: **Construction (Mid)**

Documentación completa en [`/aidlc-docs/`](./aidlc-docs/):
- [Requirements](./aidlc-docs/requirements/)
- [User Stories](./aidlc-docs/story-artifacts/USER_STORIES.md)
- [Domain Model](./aidlc-docs/design-artifacts/DOMAIN_MODEL.md)
- [Architecture](./aidlc-docs/design-artifacts/ARCHITECTURE.md)
- [ADRs](./aidlc-docs/design-artifacts/ADR/)
- [Testing Strategy](./aidlc-docs/testing/TEST_STRATEGY.md) (cobertura real: 31%)
- Deployment / Operations: aún no aplican — ver placeholders en
  [`aidlc-docs/deployment/`](./aidlc-docs/deployment/) y
  [`aidlc-docs/operations/`](./aidlc-docs/operations/)

⚠️ Nota importante detectada en la auditoría: este proyecto **no tiene control de
versiones** (`git init` pendiente). Ver [`00_PROJECT_METADATA.md`](./aidlc-docs/00_PROJECT_METADATA.md).

Última auditoría: 2026-07-30
