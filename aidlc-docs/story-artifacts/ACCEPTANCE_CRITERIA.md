# Acceptance Criteria

Criterios derivados de las historias en `USER_STORIES.md`, verificados contra comportamiento
real observado en la corrida de prueba de esta sesión (`input/productos.csv`, 8 productos,
100% encontrados) salvo donde se indique lo contrario.

## US-01 — Importación
- [x] Acepta `.xlsx`, `.csv`, `.txt` — implementado en `importer.py::_read_any`.
- [x] Reconoce encabezados en español o inglés (`Nombre`/`Producto`, `Marca`, `EAN`, etc.).
- [x] Ignora filas sin nombre ni SKU.
- [ ] ⚠️ No verificado: comportamiento con archivos `.xlsx` reales de gran tamaño (solo se
  probó `.csv` en esta sesión). Recomendado probar con un Excel real antes de producción.

## US-02/US-03 — Marca y normalización
- [x] Detecta marca por substring exacto (ej. "VERTIMEC" en el nombre) — confirmado en la
  corrida real (8/8 productos con marca de agroquímico detectada correctamente).
- [x] Fuzzy match como respaldo si no hay substring exacto (umbral 85).
- [x] Unidades equivalentes (1L, 1 LITRO, 1.0L) convergen al mismo texto vía reglas regex
  — confirmado con test automatizado (`tests/test_normalizer.py`).
- [ ] La normalización NO reconstruye información de negocio ausente en el texto original
  (ver limitación documentada en US-03). Esto es un límite conocido, no un bug.

## US-05/US-06 — Búsqueda y ranking
- [x] Construye consultas en cascada: `{marca} {nombre}` → `{nombre}` → `{nombre} Chile` →
  `{nombre} distributor` → `site:{marca}.cl/.com {nombre}`.
- [x] No duplica el token de marca si ya está en el nombre normalizado (bug real encontrado
  y corregido durante el build: la primera versión generaba "VERTIMEC VERTIMEC 1.8 EC 1 LT").
- [x] Score 0-100 combinando resolución, prioridad de dominio, fondo blanco, centrado,
  ausencia de marca de agua — confirmado con `tests/test_ranking.py` y con scores reales
  observados en la corrida (61.0 a 79.0 en el lote de prueba).
- [ ] ⚠️ No hay umbral de cobertura mínima aceptado formalmente por el negocio (ver
  `requirements/INTENT.md`, Success Metrics).

## US-07 — Verificación IA
- [x] Verificador heurístico siempre disponible sin costo — confirmado, produjo
  `ai_verified=1` con `ai_confidence=1.0` en los 8 productos de prueba.
- [ ] ⚠️ Verificador de visión real (Anthropic) implementado en código
  (`verifier.py::AnthropicVisionVerifier`) pero **no ejecutado en esta sesión** por no haber
  `ANTHROPIC_API_KEY` configurada. Requiere prueba dedicada antes de considerarlo validado.

## US-08 — Deduplicación
- [x] Hash SHA-256 del contenido descargado, persistido en `cache/image_hashes.json`.
- [x] Si el hash ya existe, se descarta el candidato y se prueba el siguiente. No se
  probó explícitamente con dos productos que compartan la misma imagen en esta sesión
  (el lote de prueba no tenía duplicados reales) — comportamiento verificado por lectura
  de código, no por caso de prueba end-to-end.

## US-09 — Optimización
- [x] Genera WebP + 4 tamaños de thumbnail — confirmado, 5 variantes por producto en la
  corrida real (`5 variantes generadas` en logs).
- [ ] PNG transparente: código presente pero depende de `rembg`, no instalado en el
  entorno de prueba — **no ejecutado, no verificado**.

## US-10 — Reporte
- [x] `catalogo.csv` con todas las columnas esperadas — confirmado, archivo real generado
  e inspeccionado.
- [x] `reporte.html` con miniaturas, badges de estado, score, enlace a fuente — confirmado
  visualmente vía captura de pantalla en navegador durante el build (100% cobertura, 8/8).

## US-11 — Persistencia / idempotencia
- [x] `has_image()` consulta SQLite antes de rebuscar — confirmado por lectura de código
  en `pipeline.py::process_product`. No se corrió una segunda vez el pipeline sobre el
  mismo input en esta sesión para confirmar el skip en runtime — recomendado como
  siguiente prueba.
