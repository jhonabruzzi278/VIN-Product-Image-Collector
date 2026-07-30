# Test Coverage Report

**Comando ejecutado realmente en esta sesión:**
```
pytest -q --cov=src/vin_collector --cov-report=term-missing
```
(se instaló `pytest-cov` para poder correrlo — no estaba en el entorno original)

## Resultado real (no estimado)

```
Name                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
src\vin_collector\__init__.py             1      0   100%
src\vin_collector\brand_detector.py      38     11    71%   23, 26-27, 35, 48-49, 55-56, 64-66
src\vin_collector\classifier.py          30      5    83%   21, 25, 42-44
src\vin_collector\cli.py                 32     32     0%   3-59
src\vin_collector\config.py              38      3    92%   28, 32, 36
src\vin_collector\database.py            51     51     0%   3-162
src\vin_collector\downloader.py          68     68     0%   7-116
src\vin_collector\importer.py            47      9    81%   45, 48-55, 79
src\vin_collector\models.py              56      2    96%   30, 74
src\vin_collector\normalizer.py          46      4    91%   60, 81-83
src\vin_collector\optimizer.py           42     42     0%   3-65
src\vin_collector\pipeline.py            84     84     0%   8-118
src\vin_collector\ranking.py             94     63    33%   28, 33, 35, 37, 71-98, 103-113, 122-136, 141-152, 156-160
src\vin_collector\report.py              36     36     0%   3-130
src\vin_collector\retry.py               24     24     0%   3-32
src\vin_collector\search_engine.py       92     92     0%   9-139
src\vin_collector\verifier.py            50     50     0%   8-101
-------------------------------------------------------------------
TOTAL                                   829    576    31%
```

## Lectura del resultado

- **Módulos bien cubiertos (>80%)**: `models.py`, `config.py`, `normalizer.py`,
  `importer.py`, `classifier.py` — la lógica de datos "pura" (sin I/O externo) está
  razonablemente probada.
- **Módulo parcialmente cubierto**: `ranking.py` (33%) — se prueba el ordenamiento
  relativo (`rank_candidates`), pero no las funciones de análisis visual con Pillow
  (`_estimate_white_background`, `_estimate_centered_subject`, `_estimate_no_watermark`,
  `refine_score_with_bytes`), que sí se ejercitaron manualmente en la corrida real pero no
  tienen aserciones automatizadas.
- **Módulos en 0%**: todo lo que hace I/O externo real (red, filesystem de imágenes, SQLite,
  CLI) — `cli.py`, `database.py`, `downloader.py`, `optimizer.py`, `pipeline.py`,
  `report.py`, `retry.py`, `search_engine.py`, `verifier.py`. Esto **no significa que no
  funcionen** — se verificaron manualmente end-to-end en esta misma sesión — significa que
  no hay una red de seguridad automatizada si alguien los modifica después.

## Umbral objetivo

⚠️ No documentado por el equipo/negocio. No se inventa un número aquí — se recomienda que
el Product Owner o el equipo técnico defina un umbral mínimo (ej. 70-80% es común en
proyectos similares) antes de la próxima fase de Construction.
