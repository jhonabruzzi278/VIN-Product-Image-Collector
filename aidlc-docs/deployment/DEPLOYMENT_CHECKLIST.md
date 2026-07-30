# Deployment Checklist

**Estado: Pendiente — el proyecto está en fase Construction, no ha llegado a un ciclo de
deployment todavía.** No se genera un checklist completo especulativo; se documenta lo real
y lo que falta genuinamente.

## Pre-Deployment (estado real hoy)

- [x] Tests pasando localmente — 8/8, ver `testing/TEST_COVERAGE_REPORT.md`. Cobertura real 31%.
- [ ] CI/CD configurado — **no existe**. No hay `.github/workflows/`, `.gitlab-ci.yml`, ni
  ningún otro pipeline. Ejecutado únicamente de forma local en esta sesión.
- [ ] Secrets no commiteados — **no verificable de forma definitiva porque no hay `.git`**.
  Se revisó manualmente: `.env.example` no contiene valores reales, `.gitignore` excluye
  `.env` correctamente para cuando se inicialice git, y no se encontró ningún `.env` real
  en el directorio del proyecto en esta sesión. Esto es una verificación de estado actual,
  no una garantía histórica (sin git no hay forma de auditar si alguna vez existió).
- [ ] Control de versiones inicializado — **no existe**. Bloqueante real para cualquier
  checklist de deployment serio (no hay forma de hacer rollback, ni de etiquetar releases).
- [ ] Empaquetado para distribución (wheel/Docker image) — no generado en esta sesión.

## Infraestructura Detectada

**Ninguna.** No hay `Dockerfile`, `docker-compose.yml`, `terraform/`, `k8s/`, ni
`serverless.yml` en el proyecto. El sistema corre hoy como script Python local vía
`vin-collector` (entry point de `pyproject.toml`) dentro de un venv.

## Siguiente paso recomendado antes de poder completar este checklist

1. `git init` + primer commit (bloqueante para todo lo demás).
2. Decidir el target de deployment real: ¿sigue siendo una herramienta CLI que corre local/
   en un servidor batch (cron), o se espera que se convierta en un servicio con API?
   Esto determina si el siguiente paso es un `Dockerfile` simple o un rediseño con capa HTTP
   (ver nota en `design-artifacts/ARCHITECTURE.md`, "Sin capa de API HTTP").
