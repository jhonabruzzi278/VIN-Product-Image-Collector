# Incident Runbooks

Hay un primer incidente real documentado en `POST_MORTEMS/` (subida de CSV que no
actualizaba el catálogo). Lo demás sigue siendo, mayormente, notas de troubleshooting de
desarrollo — el proyecto aún no está en un ciclo de Operations con incidentes de
producción propiamente dichos.

- **Si subir un listado no cambia los contadores del dashboard**: primero verificar que
  no haya un proceso ajeno ocupando el puerto 8000 en el host
  (`Get-NetTCPConnection -LocalPort 8000` en PowerShell) — pasó una vez y hacía que las
  peticiones llegaran a un proceso random en vez de al contenedor. Si el puerto está
  limpio y sigue sin cambiar nada, revisar los logs del contenedor
  (`docker compose logs -f`) buscando `"Importados 0 productos"` — indica que el archivo
  se leyó pero ninguna fila matcheó columnas reconocidas (ver
  `POST_MORTEMS/2026-07-30-csv-bom-y-delimitador-mal-detectado.md`: causas típicas son
  BOM en el encabezado o un delimitador mal detectado en CSVs de una sola columna).
- **Si `import_products` falla con `AttributeError` sobre celdas vacías**: ya corregido en
  `importer.py` con `_clean()`, pero si reaparece en un formato de archivo nuevo, revisar
  cómo pandas está tipando esa columna (`dtype=str` no siempre previene valores `NaN`).
- **Si las búsquedas de DuckDuckGo empiezan a devolver 0 resultados de forma consistente**:
  probable rate-limiting del proveedor (no confirmado, es una hipótesis documentada en
  `design-artifacts/ADR/ADR-001-...md`) — no hay retry con backoff implementado todavía.
- **Si el reporte HTML no muestra imágenes**: verificar que `local_path` en la tabla
  `images` sea relativo a `output/` y no una ruta absoluta (bug real ya corregido una vez
  en `report.py::_row_for_template`).

Esto no reemplaza runbooks reales de operación — es contexto de depuración de desarrollo.
