# SLA Definition

**Pendiente — proyecto aún no llega a Operations.**

No hay SLA de uptime/latencia definido, ni tiene sentido definirlo todavía: hoy no es un
servicio corriendo, es una herramienta CLI ejecutada bajo demanda. El único dato de
rendimiento real disponible es observacional, no un compromiso: ~7 segundos por producto
en la corrida de prueba de 8 productos de esta sesión (búsqueda + descarga + optimización +
verificación), lo que da un orden de magnitud de referencia, no una garantía.

Cuando exista un target de Operations, definir aquí como mínimo: cobertura mínima aceptable
por corrida, tiempo máximo tolerable por lote, y qué pasa (reintento automático, alerta,
escalamiento manual) cuando no se cumple.
