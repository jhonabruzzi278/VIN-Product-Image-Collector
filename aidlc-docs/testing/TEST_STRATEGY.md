# Test Strategy

## Framework Detectado

**pytest** — confirmado en `pyproject.toml`/entorno, no un framework distinto asumido.
No hay `pytest.ini`/`pyproject.toml [tool.pytest]` con marcadores custom configurados; los
tests corren con configuración por defecto.

## Tipos de test presentes (reales)

Todos los tests actuales son **tests unitarios** con fixtures `tmp_path` de pytest para
aislar filesystem (JSON de marcas/categorías, diccionario de normalización) — no hay tests
de integración automatizados ni tests end-to-end automatizados.

| Archivo | Qué cubre | # tests |
|---|---|---|
| `test_normalizer.py` | Reglas de unidades + convergencia por fuzzy matching | 2 |
| `test_brand_detector.py` | Detección de marca por substring y caso "no encontrado" | 2 |
| `test_classifier.py` | Clasificación por keywords, incluida categoría "Otros" por defecto | 1 |
| `test_importer.py` | Import desde CSV + error en archivo inexistente | 2 |
| `test_ranking.py` | Un candidato de mayor resolución/prioridad de dominio rankea primero | 1 |

**Total: 8 tests, todos pasando (verificado ejecutando `pytest -q` en esta sesión).**

## Lo que SÍ se verificó, pero no como test automatizado

El flujo completo (búsqueda real → descarga real → optimización → verificación → reporte)
se ejecutó y verificó **manualmente en esta sesión** contra internet real y se confirmó
visualmente en navegador. Es evidencia real de que el sistema funciona end-to-end, pero
**no es repetible automáticamente** — no hay un test de integración que lo re-ejecute y
falle si algo se rompe después. Es la brecha de testing más importante del proyecto.

## Gaps de test genuinos (módulos sin ningún test)

`cli.py`, `database.py`, `downloader.py`, `optimizer.py`, `pipeline.py`, `report.py`,
`retry.py`, `search_engine.py`, `verifier.py` — 0% de cobertura por test automatizado
(ver `TEST_COVERAGE_REPORT.md` para el detalle línea por línea).

## Recomendación de estrategia futura (no implementada, propuesta)

1. **Tests de `database.py`** con una BD SQLite en `tmp_path` — es el más barato de cubrir
   y el más riesgoso de dejar sin cubrir (es la fuente de verdad del catálogo).
2. **Test de integración del pipeline con proveedores fake** — crear un `FakeSearchProvider`
   y un `FakeVerifier` (ambos ya son interfaces `ABC`, listas para mockear) para probar
   `pipeline.process_product` sin depender de internet real ni de scores no determinísticos.
3. **Test de `report.py`** — generar el HTML/CSV contra una BD de prueba y verificar
   estructura (no verificar renderizado visual, eso ya se hizo manualmente).
4. Un test explícito para el caso de colisión de `Product.key` documentado en
   `code-generation/CODE_REVIEW_NOTES.md`, antes o después de decidir cómo resolverlo.
