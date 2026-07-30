# Monitoring Setup

**Pendiente — proyecto aún no llega a Operations.**

Lo único cercano a observabilidad hoy es logging local vía `loguru`
(`logs/collector.log`, rotación 5MB, retención 5 archivos — configurado en `cli.py::_setup_logging`,
real y verificado en el código, no aspiracional). No hay monitoring remoto, métricas,
dashboards, ni alerting de ningún tipo.

Cuando el proyecto tenga un target de deployment definido (ver
`deployment/DEPLOYMENT_CHECKLIST.md`), este documento debe definir: qué métricas importan
(ej. % cobertura por corrida, tasa de error de descarga, latencia por producto), dónde se
centralizan los logs, y qué dispara una alerta.
