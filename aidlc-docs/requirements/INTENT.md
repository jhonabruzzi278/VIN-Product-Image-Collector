# Project Intent

## High-Level Purpose

**Fuente: brief funcional original proporcionado por el usuario (real, no inferido).**

Construir un sistema — VIN Product Image Collector — que tome un listado de productos
(Excel/CSV/TXT) y devuelva un catálogo completo con imágenes verificadas: normalizadas,
clasificadas por categoría, con marca detectada, buscadas por prioridad de fuente
(fabricante > distribuidor > marketplace > tienda > genérico), rankeadas por calidad,
descargadas, deduplicadas, optimizadas en múltiples formatos/tamaños, verificadas por
IA de que corresponden al producto correcto, y reportadas con métricas de cobertura.

## Business Objectives

Del brief original:
1. Eliminar el trabajo manual de buscar/curar imágenes de producto para catálogos de e-commerce.
2. Garantizar calidad de imagen consistente (fondo blanco, producto centrado, alta resolución,
   sin marca de agua) mediante un sistema de ranking objetivo.
3. Priorizar fuentes con mejor licencia/confiabilidad (fabricante y distribuidor autorizado)
   antes que fuentes genéricas, para reducir riesgo legal y mejorar calidad de marca.
4. Construir una base de conocimiento reutilizable (`marcas.json`, `categorias.json`,
   caché de búsquedas, catálogo SQLite) que crezca con el uso y evite rebuscar productos ya resueltos.

## Success Metrics

Del brief original (ejemplo de reporte esperado, Módulo 12):
- **Cobertura** = productos_encontrados / productos_totales. El brief usa como ejemplo
  "534 productos, 497 encontrados, 37 pendientes, 93.1% cobertura" — esto es un **ejemplo
  ilustrativo del formato de reporte**, no una meta numérica confirmada para este proyecto.
- ⚠️ No documentado — no hay una meta de cobertura mínima aceptada, ni SLA de tiempo de
  procesamiento, definidos explícitamente por el Product Owner. Requiere validación humana.

## Constraints

### Technical
Del brief original, sección "Tecnologías recomendadas": Python 3.12, Playwright, httpx,
BeautifulSoup4/lxml, RapidFuzz, Pillow, OpenCV, SQLite/PostgreSQL, Typer, Loguru, Pydantic.

**Lo que realmente se implementó** (extraído del código, ver `design-artifacts/LOGICAL_DESIGN.md`
para el detalle): se usó SQLite (no PostgreSQL), DuckDuckGo vía `ddgs` como buscador por
defecto (no Google/Bing/Playwright), y no se usó BeautifulSoup4/lxml/OpenCV/Playwright
pese a estar declarados como dependencias opcionales — quedaron sin uso real en el código.
Esto es una **decisión pragmática documentada**, no una desviación oculta: `ddgs` no
requiere API key ni navegador, lo cual resolvía el requisito "sin credenciales" de un
build greenfield.

### Business
⚠️ No documentado — el brief no especifica presupuesto, plazos, o restricciones legales/
licencias explícitas más allá de "prioriza fuentes con mejor licencia". Requiere validación
del Product Owner (VIN Studio).

## Visión de evolución (del brief original)

El brief explícitamente pide no limitar el alcance a solo imágenes, sino evolucionar hacia
un "motor de enriquecimiento de catálogos" que también complete: descripción corta/larga,
especificaciones técnicas, peso/dimensiones, presentación, fichas técnicas PDF, hojas MSDS/SDS,
URL oficial del fabricante, etiquetas SEO, texto alt, y exportación a WooCommerce/Shopify/
Prestashop/CSV. **Ninguna de estas extensiones está implementada aún** — es la dirección de
producto declarada, no trabajo en curso.
