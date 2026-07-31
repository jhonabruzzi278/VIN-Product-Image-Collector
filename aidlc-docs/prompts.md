# AI Prompts Used (Audit Trail)

## Sesión 1: Build inicial del producto
**Fecha:** 2026-07-30
**Prompt:** Brief funcional en español (12 módulos: Importador, Normalizador, Detector de
marca, Clasificador, Buscador Inteligente, Ranking, Descarga, Optimizador, IA de
verificación, Base de datos, Reintentos, Reporte) + arquitectura de carpetas + tecnologías
recomendadas + visión de evolución hacia motor de enriquecimiento de catálogos.
**Resumen:** Se generó el proyecto completo (`src/vin_collector/`, 17 módulos, 1520 líneas),
tests (8, todos pasando), `input/productos.csv` de ejemplo, y se verificó end-to-end en vivo
contra internet real: 8/8 productos con imagen encontrada, descargada, optimizada y
verificada; reporte HTML confirmado visualmente en navegador. Se encontraron y corrigieron
3 bugs reales durante la verificación (ver `code-generation/CODE_REVIEW_NOTES.md`).
**Fase resultante:** Construction (desde Inception implícito en el brief).

## Sesión 2: Kickoff AI-DLC — análisis retroactivo y generación de aidlc-docs/
**Fecha:** 2026-07-30 (misma fecha, sesión posterior)
**Prompt:** Documento `AI_DLC_KICKOFF_PROMPT.md` proporcionado por el usuario vía ruta de
archivo local (`C:\Users\jonat\Downloads\AI_DLC_KICKOFF_PROMPT.md`), instruyendo: analizar
el proyecto a fondo, detectar fase AI-DLC, auditar documentación existente vs. faltante,
generar `/aidlc-docs/` con información real (no genérica), actualizar `README.md`, y
presentar resumen ejecutivo — todo de forma autónoma sin confirmación paso a paso.
**Resumen:** Se detectó fase Construction (Mid), con la salvedad documentada de que la
lectura literal del árbol de decisión del propio kickoff prompt apuntaba a "MIXED" — se
optó por la clasificación más específica de la tabla de señales, y se dejó explícito como
supuesto. Se generó la estructura completa de `aidlc-docs/` para Inception + Construction
(11 documentos + 1 ADR), y placeholders honestos ("Pendiente") para Deployment/Operations,
ya que el proyecto genuinamente no ha llegado ahí. Se ejecutó `pytest --cov` real para
obtener el número real de cobertura (31%) en vez de estimarlo. Se identificó y documentó
como hallazgo real: el proyecto no tiene control de versiones (`.git`) — esto se registró
en `00_PROJECT_METADATA.md` como bloqueante para varios ítems del checklist de Construction
y Deployment.
**Fase resultante:** Sin cambio (Construction) — esta sesión fue de documentación, no de
código nuevo, tal como indicaba la regla "nunca sobrescribas código fuente del proyecto".

## Sesión 3: Interfaz web + Docker
**Fecha:** 2026-07-30 (misma fecha, sesión posterior)
**Prompt:** "quiero alguna interfaz grafica sencilla web y que todo este dockerizado".
**Resumen:** Se construyó `src/vin_collector/web.py` (FastAPI) sobre el mismo pipeline que
ya usaba el CLI — subida de listado, job en segundo plano, progreso en vivo vía polling
del mismo SQLite, y servido del reporte/catálogo. Se dockerizó con `Dockerfile` +
`docker-compose.yml` (volúmenes para persistir input/output/cache/database/logs/config
fuera del contenedor). Verificado de extremo a extremo tanto local (`uvicorn` directo)
como dentro del contenedor real construido con `docker compose build`. Se encontró y
corrigió un bug real de compatibilidad de rutas Windows/Linux en `report.py` al compartir
el mismo SQLite entre host y contenedor vía volumen. Commiteado y pusheado
(`e8aa75d Add web UI (FastAPI) and Docker support`).
**Fase resultante:** Sin cambio (Construction) — nueva superficie (web UI), mismo dominio.

## Sesión 4: Mejoras de reporte + bug real de importación de CSV
**Fecha:** 2026-07-30 (misma fecha, sesión posterior)
**Prompts:** (a) "quiero que pueda ver mas grande el preview de las fotos y boton para
descargar la imagen"; (b) "estoy intentando cargar otro csv pero no me actualiza lo toma
como si fuera el mismo revisa ese error testealo documentalo solucionalos commitea y
pushea".
**Resumen:** (a) se agrandó el preview de 48px a 140px con hover y se agregó un botón de
descarga directa por producto en `reporte.html`. (b) Se investigó el reporte de bug del
usuario de forma empírica (no especulativa): se reprodujo con su archivo real, se
encontraron **dos causas raíz independientes** — un proceso ajeno ocupando el puerto 8000
en el host (infraestructura, no código) y un bug real en `importer.py` donde un CSV
exportado con BOM UTF-8 y una sola columna hacía que `import_products` devolviera 0
productos silenciosamente (el `csv.Sniffer` de pandas "inventaba" un delimitador a partir
de letras repetidas en el encabezado). Corregido con lectura `utf-8-sig` + detección de
delimitador acotada a candidatos conocidos + fallback explícito a una sola columna con
parsing consciente de comillas. Se agregaron 5 tests de regresión y se verificó el fix
contra el contenedor Docker real reconstruido (101 → 106 productos tras subir una muestra
real). Documentado en detalle en
`operations/POST_MORTEMS/2026-07-30-csv-bom-y-delimitador-mal-detectado.md`. Se detectó
que `input/productos.csv` había quedado con el catálogo real del usuario (469 productos de
negocio) apuntando a subirse a un repo público — se consultó al usuario, quien eligió
excluirlo del commit; se movió el ejemplo genérico a `input/ejemplo_productos.csv` y se
actualizó `.gitignore` para que datos reales de catálogo no vuelvan a colarse por defecto.
**Fase resultante:** Sin cambio (Construction) — primer incidente real post-deploy,
resuelto y documentado con post-mortem.
