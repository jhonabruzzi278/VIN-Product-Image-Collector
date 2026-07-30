# Architecture Overview

## Estructura del Proyecto (real, generada por inspección de directorios)

```
VIN Product Image Collector/
├── input/                  # Listados de productos a procesar (xlsx/csv/txt)
├── output/
│   ├── images/              # Imagen original + WebP por producto
│   ├── thumbnails/           # Miniaturas 200/400/800/1200 px
│   ├── catalogo.csv          # Catálogo tabular final
│   └── reporte.html          # Reporte visual con cobertura
├── cache/                  # Diccionario de normalización, hashes de imagen (dedupe)
├── database/                # catalog.db (SQLite) — productos, imágenes, caché de búsquedas
├── logs/                   # collector.log (rotación 5MB, retención 5 archivos)
├── config/                 # marcas.json, categorias.json, dominios_prioridad.json
├── src/vin_collector/       # Código fuente (17 módulos, 1520 líneas totales)
├── tests/                  # 5 archivos de test, 8 tests, pytest
├── aidlc-docs/              # Esta documentación
├── pyproject.toml / requirements.txt
└── README.md
```

## Tech Stack

Ver tabla completa en [`LOGICAL_DESIGN.md`](./LOGICAL_DESIGN.md#stack-tecnológico-detectado-por-import-real-no-por-lo-declarado-en-requirementstxt).

## Decisiones Arquitectónicas Detectadas

- **Monolito CLI de un solo proceso**, no microservicios — coherente con el volumen de
  trabajo esperado (catálogos de cientos de productos, no streaming en tiempo real).
- **Procesamiento síncrono, secuencial, producto por producto** (`pipeline.py` es un `for`
  simple). No hay paralelismo ni async pese a que `httpx` soporta async — decisión
  pragmática para un build inicial, pero es el cuello de botella más obvio para catálogos
  grandes (534 productos como en el ejemplo del brief tomarían, extrapolando el ritmo real
  observado de ~7s/producto en la corrida de prueba, **~1 hora** en serie).
- **SQLite como única fuente de verdad**, no PostgreSQL pese a que el brief lo sugería como
  alternativa — apropiado para un solo proceso local; sería el primer punto a migrar si el
  sistema pasa a correr en múltiples workers concurrentes (SQLite tiene limitaciones serias
  de escritura concurrente).
- **Sin capa de API HTTP** — es una herramienta CLI, no un servicio. Si "Operations" llega
  a aplicar (deploy como servicio), esto es un cambio arquitectónico, no una extensión menor.
- **Todas las credenciales opcionales vía `.env`**, nunca hardcodeadas — verificado por
  lectura de `config.py` y confirmado que `.env` está en `.gitignore` (aunque, de nuevo,
  no hay `.git` real todavía para que ese `.gitignore` proteja nada en la práctica).

## Diagrama de flujo (del brief original, confirmado como implementado end-to-end)

```
Leer Excel/CSV/TXT → Normalizar nombres → Detectar marca → Clasificar categoría
→ Buscar imágenes (cascada de queries) → Rankear candidatos → Descargar (+ deduplicar)
→ Optimizar (WebP + thumbnails) → Verificar con IA → Guardar en SQLite → Reporte
                                    ↑______________________________|
                                    Reintentos con variantes más simples si no hay resultados
```

Este flujo fue **ejecutado y verificado en vivo** durante el build (8/8 productos de
`input/productos.csv`, 100% de cobertura, reporte HTML confirmado visualmente en navegador),
no es un diagrama aspiracional.
