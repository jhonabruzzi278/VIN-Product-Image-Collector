# Incident Runbooks

**Pendiente — proyecto aún no llega a Operations, no hay incidentes de producción que documentar.**

Lo más cercano a un "runbook" hoy son notas de troubleshooting derivadas de bugs reales
encontrados durante el build (ver `code-generation/CODE_REVIEW_NOTES.md`), útiles para
depuración local:

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
