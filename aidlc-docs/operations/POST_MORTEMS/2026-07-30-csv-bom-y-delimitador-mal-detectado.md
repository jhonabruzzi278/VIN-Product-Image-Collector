# Post-mortem: subir un CSV nuevo no actualizaba el catálogo

**Fecha:** 2026-07-30
**Reportado por:** usuario, vía interfaz web ("estoy intentando cargar otro csv pero no
me actualiza lo toma como si fuera el mismo")
**Severidad:** Alta — el flujo principal del producto (subir un listado y obtener
imágenes) fallaba en silencio con un archivo real de un proveedor, sin ningún error
visible para el usuario.
**Estado:** Resuelto y verificado en vivo contra el contenedor Docker real.

## Síntoma

El usuario subió su propio listado de productos (469 productos reales: fertilizantes,
herbicidas, EPP, herramientas Victorinox, etc., exportado como CSV de una sola columna
"PRODUCTO") a través de la interfaz web. El dashboard no reflejó ningún cambio — mismos
contadores de antes, mismo reporte, como si la subida no hubiera pasado nada.

## Causas raíz (fueron dos, no una)

### 1. Colisión de puerto en el host (infraestructura, no código)

Un proceso Python completamente ajeno al proyecto (gestionado por `uv`, en
`C:\Users\jonat\AppData\Roaming\uv\...`) quedó escuchando en el puerto 8000 al mismo
tiempo que el contenedor Docker. Dependiendo de cuál proceso ganara el bind en Windows,
las peticiones del navegador a `localhost:8000` a veces llegaban a la app real (Docker) y
a veces a ese proceso ajeno — que ni siquiera tiene nuestras rutas, y devolvía 404.
Esto por sí solo podía explicar intentos de subida que "no hacían nada" visible.

**Mitigación aplicada:** se identificó y terminó el proceso ajeno (`Stop-Process`). No es
un fix de código — es un recordatorio operacional: antes de depurar "por qué no
funciona", verificar qué proceso real está respondiendo en el puerto usado
(`Get-NetTCPConnection -LocalPort 8000`). Ver `operations/INCIDENT_RUNBOOKS.md`.

### 2. Bug real en `importer.py` — la causa que realmente impedía el import (CRÍTICO)

Con el puerto ya limpio, se reprodujo el problema de forma determinística:

```python
from vin_collector.importer import import_products
import_products('input/productos.csv')  # -> "Importados 0 productos"
```

Dos defectos independientes en la lectura de CSV, ambos con el mismo archivo real:

**a) BOM (byte-order-mark) no removido del encabezado.**
El archivo fue exportado como "CSV UTF-8" (patrón común en exportaciones desde Excel/
ERP), lo que antepone un BOM invisible al primer carácter: el encabezado real era
`"\ufeffPRODUCTO"`, no `"PRODUCTO"`. `_normalize_headers` no reconocía esa columna
contra `COLUMN_ALIASES`, así que ninguna fila tenía `nombre_original` ni `sku`
reconocidos → **todas las filas se descartaban silenciosamente**, sin ningún error.

**b) `sep=None` (auto-detección de pandas/csv.Sniffer) adivinaba mal el delimitador
en archivos de una sola columna.** Incluso corrigiendo el BOM, con
`pd.read_csv(..., sep=None, engine="python")` el Sniffer de Python, al no encontrar un
delimitador real (el archivo es una sola columna de nombres), "inventaba" uno a partir
de letras repetidas en el encabezado: partió literalmente `"PRODUCTO"` en las columnas
`["PR", "DUCT", "Unnamed: 2"]` usando la letra **"O"** como si fuera un separador.
Resultado: la columna de nombre desaparecía por completo.

Ambos bugs, combinados, producían exactamente el síntoma reportado: 0 productos
importados, base de datos sin cambios, reporte idéntico al anterior — indistinguible de
"no pasó nada" desde la interfaz.

## Fix aplicado

En `src/vin_collector/importer.py`:

1. Todas las lecturas de CSV/TXT usan `encoding="utf-8-sig"` (retira el BOM
   automáticamente si existe, sin afectar archivos sin BOM).
2. Se reemplazó `sep=None` (auto-detección genérica, no confiable) por
   `_detect_delimiter()`: cuenta ocurrencias de un set fijo de candidatos
   (`, ; \t |`) en la línea de encabezado y elige el más frecuente; si **ninguno**
   aparece, se asume una sola columna y **no se intenta dividir en absoluto**
   (`_read_single_column_csv` / `_read_single_column_txt`).
3. La lectura de una sola columna usa `csv.reader` (no `line.strip()` ingenuo) para
   respetar comillas — un campo como `"Aceite Para Multitool, 10ml, Blister 10 ml"`
   (entrecomillado porque contiene una coma) ahora se importa sin las comillas
   literales pegadas al nombre, en vez de conservarlas (lo que habría degradado la
   calidad de las búsquedas de imagen para ese producto).

## Verificación real (no solo tests unitarios)

1. `pytest -q` — 13 tests (5 nuevos de regresión para este bug), todos pasando.
2. Reproducción directa contra el archivo real del usuario: `0` → **`469`** productos
   importados tras el fix.
3. **Verificación end-to-end contra el contenedor Docker real** (no solo en local):
   se reconstruyó la imagen (`docker compose build`), y se subió una muestra real de
   5 productos del archivo del usuario vía el endpoint `/upload` tal como lo haría el
   navegador. El contador total pasó de 101 → 106 (los 5 productos se importaron,
   buscaron, encontraron imagen y se sumaron al catálogo). Confirma que el fix
   resuelve el problema exactamente en el camino que el usuario reportó, no solo a
   nivel de función aislada.

## Lecciones / seguimiento

- **No usar `sep=None` de pandas para adivinar delimitadores en producción.** Es
  conveniente para exploración manual, pero su heurística no está diseñada para
  archivos de una sola columna y puede fallar de forma silenciosa y no obvia.
- **Los fallos de importación deben dejar de ser silenciosos.** Hoy, si 0 filas
  matchean, `import_products` simplemente retorna una lista vacía y el pipeline
  "termina exitosamente" sin procesar nada — no hay ninguna advertencia visible en la
  interfaz web de que el archivo subido no se pudo interpretar. **Recomendación para
  el próximo ciclo:** si `import_products` devuelve 0 productos pero el archivo no
  estaba vacío, superficiar un error claro en `web.py` (`_job_state["error"]`) en vez
  de dejar que se vea como "no pasó nada".
- **Datos reales de catálogo no deben terminar en un repo público sin decisión
  explícita.** Durante esta sesión, el archivo de ejemplo `input/productos.csv` había
  sido sobrescrito con el catálogo real del usuario (469 productos de negocio). Se
  excluyó del commit a pedido explícito del usuario y se movió el archivo de ejemplo a
  `input/ejemplo_productos.csv` (síntetico, genérico), con `input/*` ahora ignorado por
  `.gitignore` salvo ese ejemplo — para que esto no vuelva a pasar por accidente en
  una futura sesión.
