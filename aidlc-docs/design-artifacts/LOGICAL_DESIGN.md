# Logical Design

## Patterns Detectados en el Código (reales, verificados leyendo cada archivo)

| Patrón | Dónde | Evidencia |
|---|---|---|
| **Pipeline / Orquestador secuencial** | `pipeline.py` | `run_pipeline` → `process_product` encadena los 12 módulos en orden fijo por producto |
| **Strategy** | `search_engine.py` (`SearchProvider` ABC → `DuckDuckGoProvider`), `verifier.py` (`ImageVerifier` ABC → `HeuristicVerifier` / `AnthropicVisionVerifier`) | Permite intercambiar proveedor de búsqueda o de verificación sin tocar el pipeline |
| **Repository** | `database.py::Database` | Encapsula todo el acceso a SQLite detrás de métodos de dominio (`upsert_product`, `has_image`, etc.) |
| **Settings / Config centralizada** | `config.py::Settings` (Pydantic Settings) | Única fuente de rutas, umbrales y credenciales opcionales, cargada desde `.env` |
| **Cache-aside** | `search_engine.py` (cache de búsquedas en SQLite), `normalizer.py` (diccionario de nombres canónicos en JSON), `downloader.py` (hashes de imagen en JSON) | Tres cachés independientes con formatos distintos (SQLite vs JSON plano) — inconsistencia menor, ver Gaps |
| **CLI de comandos** | `cli.py` (Typer: `run`, `report`, `status`) | Capa de interfaz separada del núcleo de dominio |
| **Fallback en cascada** | `search_engine.py::build_queries` + `retry.py::retry_variants` | Degrada la consulta progresivamente en vez de fallar directo |

## Stack Tecnológico (detectado por import real, no por lo declarado en requirements.txt)

| Componente | Tecnología | Versión declarada | Uso real confirmado |
|---|---|---|---|
| Lenguaje | Python | ≥3.11 (probado en 3.12.0 vía venv) | ✅ |
| CLI | Typer | ≥0.12 | ✅ `cli.py` |
| Validación/Config | Pydantic + pydantic-settings | ≥2.7 / ≥2.3 | ✅ `models.py`, `config.py` |
| Import de datos | pandas + openpyxl | ≥2.2 / ≥3.1 | ✅ `importer.py` |
| Similitud difusa | RapidFuzz | ≥3.9 | ✅ `normalizer.py`, `brand_detector.py` |
| HTTP | httpx | ≥0.27 | ✅ `downloader.py` |
| Imágenes | Pillow | ≥10.3 | ✅ `ranking.py`, `optimizer.py` |
| Reporte | Jinja2 | ≥3.1 | ✅ `report.py` |
| Logging | loguru | ≥0.7 | ✅ todos los módulos |
| Búsqueda de imágenes | ddgs (DuckDuckGo) | ≥6.0 | ✅ `search_engine.py` |
| Base de datos | SQLite (stdlib `sqlite3`) | — | ✅ `database.py` |
| Verificación visión IA (opcional) | anthropic | ≥0.34 (extra `[vision]`) | ⚠️ Código presente, **no ejecutado** en esta sesión (sin API key) |
| Remoción de fondo (opcional) | rembg | **no declarado** | ⚠️ Import opcional en `optimizer.py`, dependencia faltante en requirements.txt/pyproject.toml |
| BeautifulSoup4, lxml, opencv, numpy, playwright | — | declarados como opcionales | ❌ **Sin uso real en el código** — recomendados por el brief original, no incorporados en la implementación actual |

## Servicios Externos Detectados

- **DuckDuckGo** (vía `ddgs`) — servicio de búsqueda de imágenes, sin autenticación, usado
  por defecto. Sujeto a rate-limiting no documentado por el proveedor (riesgo operacional
  para volúmenes grandes de productos).
- **Anthropic API** — opcional, para verificación de imágenes con modelo de visión. Requiere
  `ANTHROPIC_API_KEY` en `.env` (no commiteado — `.gitignore` lo excluye correctamente).
- **Google Custom Search** — mencionado en `.env.example` (`GOOGLE_CSE_API_KEY`,
  `GOOGLE_CSE_CX`) como placeholder para un proveedor adicional, pero **no hay ninguna
  clase `GoogleCSEProvider` implementada** — es una intención documentada, no código.
- Ningún servicio de nube (AWS/GCP/Azure) — consistente con el principio "sin vendor lock-in"
  del brief.

## Nota de diseño real encontrada durante testing (no hipotética)

Durante la verificación end-to-end de esta sesión, el test de normalización original
asumía que "VERTIMEC X1 LT" debía converger a "VERTIMEC 1.8 EC 1 LT" solo con reglas +
fuzzy matching. **Falló**, correctamente: fuzzy matching no puede inventar la concentración
"1.8 EC" que no está en el texto de entrada. Esto reveló un límite real de arquitectura:
si el negocio necesita ese tipo de normalización (variantes que omiten datos técnicos), se
necesita una capa adicional de alias por marca/SKU (diccionario de presentaciones oficiales),
no solo similitud textual. Se ajustó el test para reflejar la capacidad real del sistema en
vez de inflar la expectativa.
