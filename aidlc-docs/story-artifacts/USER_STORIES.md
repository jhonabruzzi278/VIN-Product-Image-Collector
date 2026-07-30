# User Stories

⚠️ El brief original no está escrito como historias de usuario — es una especificación
funcional por módulos. Las historias siguientes se **derivan** de esa especificación
(cada módulo mapea a 1+ historia), verificadas contra el código real para marcar estado.

## Épica: Importación y enriquecimiento de datos

**US-01** — Como gestor de catálogo, quiero subir un Excel/CSV/TXT con mis productos para
no tener que re-escribir el listado en otro formato.
*Estado: ✅ Hecho — `importer.py`, encabezados flexibles en español/inglés.*

**US-02** — Como gestor de catálogo, quiero que el sistema infiera la marca cuando no la
escribí, para no tener que completarla a mano en cientos de filas.
*Estado: ✅ Hecho — `brand_detector.py`.*

**US-03** — Como gestor de catálogo, quiero que nombres mal escritos o con formato
inconsistente ("VERTIMEC 1L" vs "VERTIMEC X1 LT") se normalicen automáticamente.
*Estado: ✅ Hecho para variantes de formato/unidades. ⚠️ Limitación real encontrada durante
testing: la normalización por reglas + fuzzy matching **no puede** inferir información de
negocio ausente (ej. no puede saber que "VERTIMEC 1LT" debería llevar "1.8 EC" si esa
concentración no aparece en el texto) — ver nota en `design-artifacts/LOGICAL_DESIGN.md`.*

**US-04** — Como gestor de catálogo, quiero que cada producto se clasifique en una
categoría (Fitosanitario, EPP, Riego, Semillas, etc.) sin tener que hacerlo manualmente.
*Estado: ✅ Hecho — `classifier.py`, basado en keywords configurables.*

## Épica: Búsqueda y verificación de imágenes

**US-05** — Como gestor de catálogo, quiero que el sistema busque primero en el sitio del
fabricante y solo baje de prioridad a fuentes genéricas si no encuentra nada, para reducir
riesgo de licencias y mejorar calidad de marca.
*Estado: ✅ Hecho — cascada de consultas + ranking por prioridad de dominio.*

**US-06** — Como gestor de catálogo, quiero que las imágenes candidatas se puntúen
objetivamente (resolución, fondo blanco, centrado, sin marca de agua) para no tener que
revisar cada una a mano.
*Estado: ✅ Hecho, con matiz: "marca visible" y "imagen reciente" del brief original
**no están implementados** como señales de scoring.*

**US-07** — Como gestor de catálogo, quiero que una IA confirme que la imagen descargada
realmente corresponde al producto, para evitar publicar la foto de otra presentación.
*Estado: ✅ Hecho con dos niveles: heurístico (gratis, siempre activo) y visión real vía
Anthropic (opcional, requiere API key, no probado en esta sesión por falta de credencial).*

**US-08** — Como gestor de catálogo, quiero que no se descarguen imágenes duplicadas para
distintos productos.
*Estado: ✅ Hecho — deduplicación por hash de contenido.*

## Épica: Salida y reutilización

**US-09** — Como gestor de catálogo, quiero las imágenes optimizadas en varios tamaños
(thumbnail, mediano, grande) y en WebP, listas para subir a una tienda online.
*Estado: ✅ Hecho — 200/400/800/1200px + WebP. PNG transparente opcional, con gap de
dependencia no declarada (ver `requirements/REQUIREMENTS.md`).*

**US-10** — Como gestor de catálogo, quiero un reporte final con el % de cobertura para
saber cuántos productos quedaron pendientes de revisión manual.
*Estado: ✅ Hecho — `reporte.html` + `catalogo.csv`. Verificado visualmente en navegador
durante el build (no solo probado por consola).*

**US-11** — Como gestor de catálogo, quiero volver a correr el proceso sobre el mismo
listado sin que rebusque productos ya resueltos.
*Estado: ✅ Hecho — SQLite persiste estado, `has_image()` evita reprocesar.*

## Épica futura (declarada en el brief, no implementada)

**US-12 (futura)** — Como gestor de catálogo, quiero que el sistema también complete
descripciones, specs técnicas, fichas PDF/MSDS y exporte a WooCommerce/Shopify/Prestashop.
*Estado: ⚠️ No implementado — dirección de producto declarada en el brief, sin código aún.*
