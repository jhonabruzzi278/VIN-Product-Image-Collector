# ADR-001: DuckDuckGo (vía `ddgs`) como proveedor de búsqueda de imágenes por defecto

**Estado:** Aceptada (implementada y verificada en la corrida de prueba de esta sesión)
**Fecha:** 2026-07-30
**Contexto de la sesión:** decisión tomada durante el build inicial (greenfield), no una
decisión retroactiva documentada después — se registra ahora porque no existía `aidlc-docs/`
en el momento de tomarla.

## Contexto

El brief original (Módulo 5, "Buscador Inteligente") no prescribe un motor de búsqueda
específico, pero la sección de "Tecnologías recomendadas" sugiere Playwright para
navegación/descarga. El entorno de build era greenfield y no tenía credenciales de ningún
proveedor de búsqueda pagado (Google Custom Search, Bing, SerpAPI) disponibles. El sistema
debía quedar **funcional de punta a punta sin requerir que el usuario configure nada** antes
de la primera corrida.

## Decisión

Usar la librería `ddgs` (DuckDuckGo Search) como `SearchProvider` por defecto — búsqueda de
imágenes vía HTTP, sin API key, sin necesidad de instalar/lanzar un navegador con Playwright.
Se diseñó `SearchProvider` como clase abstracta (`search_engine.py`) específicamente para que
esta no sea una decisión permanente: agregar un `GoogleCSEProvider` más adelante es una
implementación nueva de la interfaz, no un rediseño.

## Alternativas consideradas

1. **Google Custom Search API** — mejor control de resultados y dominios permitidos, pero
   requiere API key + Custom Search Engine ID configurados por el usuario antes de poder
   correr nada. Se dejó como placeholder en `.env.example` para una futura implementación.
2. **Playwright + scraping directo de Google Images** — más frágil (rompe con cambios de
   markup de Google, más lento por lanzar navegador), y añade una dependencia pesada
   (descarga de binarios de navegador) al primer `pip install`. Se dejó como dependencia
   opcional (`[browser]` extra) sin implementación activa.
3. **DuckDuckGo vía `ddgs`** — elegida. Sin credenciales, sin navegador, HTTP simple.

## Consecuencias

**Positivas (confirmadas en la corrida real):**
- Cero fricción de setup — la corrida de prueba encontró imágenes reales para 8/8 productos
  sin ninguna configuración de credenciales.
- Dependencia liviana (`ddgs` es un paquete HTTP puro).

**Negativas / riesgos (documentados, no verificados a fondo aún):**
- DuckDuckGo no tiene un SLA público ni límites de rate documentados oficialmente para este
  uso — para catálogos grandes (cientos/miles de productos) existe riesgo real de
  rate-limiting o bloqueo temporal, no probado en esta sesión (el lote de prueba fue de
  solo 8 productos).
- Menor control sobre qué dominios aparecen en los resultados comparado con Google CSE
  (que permite restringir a una lista de sitios). Se compensa parcialmente con
  `DomainPriorityRanker` (post-filtrado por prioridad), pero no es un filtro de entrada.
- Sin API key no hay garantía contractual de disponibilidad del servicio — es un riesgo
  aceptado explícitamente para la fase actual (Construction), a revisar antes de Operations
  si el volumen de productos crece significativamente.

## Revisitar cuando

- El catálogo a procesar supere ~100-200 productos por corrida (validar rate-limiting real).
- El negocio necesite restringir búsquedas a una lista blanca de dominios de forma estricta
  (no solo post-ranking).
- Haya presupuesto/decisión de negocio para pagar Google Custom Search o SerpAPI.
