# Requirements

Extraídos del brief funcional original (real) y contrastados contra el código implementado
en `src/vin_collector/` (real, verificado leyendo cada módulo).

## Funcionales

| # | Requisito (brief original) | Estado real en código |
|---|---|---|
| R1 | Importar productos desde Excel, CSV o TXT | ✅ Implementado — `importer.py`, soporta `.xlsx/.xls/.csv/.txt` |
| R2 | Inferir marca si falta en el listado | ✅ Implementado — `brand_detector.py`, matching exacto + difuso vs `config/marcas.json` |
| R3 | Normalizar nombres de producto con variantes de unidades/formato | ✅ Implementado — `normalizer.py`, reglas regex + RapidFuzz contra diccionario aprendido en `cache/normalizer_dictionary.json` |
| R4 | Clasificar categoría automáticamente | ✅ Implementado — `classifier.py`, keywords en `config/categorias.json` |
| R5 | Construir consultas de búsqueda escalonadas (fabricante → distribuidor → genérica → site:) | ✅ Implementado — `search_engine.py::build_queries` |
| R6 | Priorizar fuentes: fabricante > distribuidor > marketplace > tienda > Google Images | ✅ Implementado — `DomainPriorityRanker` en `search_engine.py`, dominios en `config/dominios_prioridad.json` |
| R7 | Rankear candidatos por resolución, fondo blanco, centrado, marca visible, reciente, sin marca de agua | ⚠️ Parcial — implementadas resolución, prioridad de dominio, fondo blanco (heurístico), centrado (heurístico), sin-marca-de-agua (heurístico). **"Marca visible" y "reciente" NO están implementados** — no hay señal de fecha de imagen ni detección de logo. |
| R8 | Descargar y registrar fuente/URL/fecha/resolución | ✅ Implementado — `downloader.py` + tabla `images` en `database.py` |
| R9 | Eliminar duplicados | ✅ Implementado — dedupe por hash SHA-256 de contenido en `downloader.py` (`cache/image_hashes.json`) |
| R10 | Optimizar: WebP, thumbnails (200/400/800/1200), PNG transparente opcional | ✅ Implementado — `optimizer.py`. PNG transparente depende de `rembg`, que es **import opcional no declarado en requirements.txt** (gap real, ver Gaps abajo) |
| R11 | Verificación por IA de que la imagen corresponde al producto | ✅ Implementado con fallback — `verifier.py`: heurístico por defecto (sin costo), y `AnthropicVisionVerifier` real si hay `ANTHROPIC_API_KEY`. No se probó el camino con Anthropic en esta sesión (sin API key disponible). |
| R12 | Base de datos para no rebuscar productos ya resueltos | ✅ Implementado — SQLite (`database.py`), `has_image()` se consulta antes de rebuscar |
| R13 | Reintentos con variantes progresivamente más simples | ✅ Implementado — `retry.py` + integración en `pipeline.py` |
| R14 | Reporte final con métricas de cobertura | ✅ Implementado — `report.py`, genera `catalogo.csv` + `reporte.html`. **Verificado visualmente en navegador en la sesión de build** (screenshot confirmado, no solo "debería funcionar") |

## No Funcionales

| # | Requisito | Estado |
|---|---|---|
| NF1 | Sin vendor lock-in de nube específica | ✅ Cumplido — todo corre local, sin dependencia de AWS/GCP/Azure |
| NF2 | Funcionar sin API keys de pago por defecto | ✅ Cumplido — DuckDuckGo (`ddgs`) y verificador heurístico no requieren credenciales |
| NF3 | Rendimiento / tiempo de procesamiento | ⚠️ No documentado formalmente. Dato real observado: 8 productos procesados end-to-end (búsqueda + descarga + optimización) en **~55 segundos** en la corrida de prueba de esta sesión — orden de magnitud útil para estimar, no un SLA. |
| NF4 | Cobertura de tests ≥ algún umbral | ⚠️ No documentado. Real medido: **31%** (ver `testing/TEST_COVERAGE_REPORT.md`). Sin umbral objetivo definido por el equipo. |

## Gaps genuinos identificados (no en el brief, encontrados auditando el código)

- `rembg` (para PNG con fondo transparente) se importa de forma opcional en `optimizer.py`
  pero **no está listado en `requirements.txt` ni en `pyproject.toml`** — si un usuario lo
  instala manualmente funciona; si no, la variante se omite silenciosamente (comportamiento
  intencional vía `try/except ImportError`, pero la dependencia no está documentada).
- `beautifulsoup4`, `lxml`, `opencv-python-headless`, `numpy`, `playwright` están declarados
  en `requirements.txt`/`pyproject.toml` (recomendados por el brief original) pero **no se
  importan en ningún módulo real** — quedaron como dependencias reservadas para scraping
  específico por sitio o validaciones visuales avanzadas que aún no se construyeron.
- No hay control de versiones (sin `.git`) — ver `00_PROJECT_METADATA.md`.
