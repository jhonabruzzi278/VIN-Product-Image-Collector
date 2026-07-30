# Infrastructure as Code

**Pendiente — no existe IaC en este proyecto.**

No se encontró `Dockerfile`, `docker-compose.yml`, `terraform/`, `pulumi/`, `k8s/`,
`serverless.yml`, ni ningún script de aprovisionamiento en el repositorio. El proyecto corre
hoy exclusivamente como proceso local (`python -m venv` + `pip install -e .` +
`vin-collector run ...`), documentado en `README.md`.

Esto es coherente con la fase actual (Construction, no Operations) — no es un gap a corregir
todavía, es simplemente trabajo futuro que no corresponde generar de forma especulativa.
Cuando el proyecto avance a un ciclo de deployment real, este documento debe reemplazarse
con la definición real de infraestructura elegida (contenedor simple vs. función serverless
vs. servidor batch con cron — depende de la decisión de arquitectura pendiente en
`deployment/DEPLOYMENT_CHECKLIST.md`).
