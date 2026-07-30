# Code Review Notes

No existe un proceso de code review formal (sin `.git`, sin PRs, sin branch protection —
ver `00_PROJECT_METADATA.md`). Lo siguiente es una **auto-revisión real** hecha durante el
build, con hallazgos concretos encontrados y corregidos, no una checklist genérica.

## Hallazgos reales encontrados y corregidos en esta sesión

1. **Bug de tipos — `importer.py`** (CRÍTICO, corregido)
   Celdas vacías en CSV/Excel llegaban como `float('nan')` de pandas, no como `None`, y el
   código llamaba `.strip()` sobre ellas → `AttributeError`. Encontrado por el propio
   `pytest`, no por inspección manual. Corregido con una función `_clean()` que usa
   `pd.isna()` explícitamente.

2. **Consulta de búsqueda duplicada — `search_engine.py`** (menor, corregido)
   `build_queries` generaba `"VERTIMEC VERTIMEC 1.8 EC 1 LT"` cuando la marca detectada ya
   era el primer token del nombre normalizado. Encontrado revisando los logs de la corrida
   real (no por test automatizado — gap de cobertura real). Corregido con un chequeo de
   prefijo antes de anteponer la marca.

3. **Ruta absoluta de Windows en HTML — `report.py`** (menor, corregido)
   `<img src>` con ruta absoluta `C:\Trabajos\...\imagen.jpg` no renderiza en un navegador.
   Encontrado abriendo el reporte real en el navegador (Módulo 12 verificado visualmente,
   no solo "el HTML se generó sin error"). Corregido convirtiendo a ruta relativa POSIX
   respecto a `output/`.

4. **Expectativa de test poco realista — `tests/test_normalizer.py`** (proceso, corregido)
   El test original asumía que fuzzy matching podía convertir "VERTIMEC X1 LT" en
   "VERTIMEC 1.8 EC 1 LT" — información (concentración "1.8 EC") que no existe en el texto
   de entrada. Ningún algoritmo de similitud textual puede inventar eso. Se corrigió el test
   para reflejar la capacidad real del sistema (convergencia de variantes de formato de
   unidad, no de contenido ausente) en vez de bajar el estándar del código para pasar un
   test irreal.

## Gaps de calidad NO corregidos (pendientes, documentados honestamente)

- **Cobertura de test real: 31%**. Módulos con 0% de cobertura por tests automatizados:
  `cli.py`, `database.py`, `downloader.py`, `optimizer.py`, `pipeline.py`, `report.py`,
  `retry.py`, `search_engine.py`, `verifier.py`. Estos sí se ejercitaron **manualmente**
  vía la corrida end-to-end real, pero no tienen aserciones automatizadas que fallen si
  alguien los rompe después. Ver `testing/TEST_COVERAGE_REPORT.md`.
- **Colisión de `Product.key`** — dos productos sin SKU/EAN y con el mismo nombre
  normalizado colisionan silenciosamente en la misma fila de SQLite (ver `DOMAIN_MODEL.md`).
  No hay test ni salvaguarda para este caso.
- **`rembg` no declarado como dependencia** pese a usarse opcionalmente en `optimizer.py`.
- **Sin manejo de rate-limiting/backoff** para las llamadas a DuckDuckGo — si el proveedor
  empieza a devolver errores por volumen, el código simplemente loguea un warning y sigue
  con la siguiente query, sin retry con backoff exponencial.
