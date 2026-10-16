---
tipo: decision
id: ADR-005
fecha: 2026-10-13
estado: aceptada
parametro: guard, .claude/settings.json
reemplaza: 
---
# ADR-005 · El LLM solo ve código, datos sintéticos y agregados

## Contexto
Los organizadores permiten LLMs que actúen como *Processor* (tier Business/API, sin entrenamiento) y piden
una interpretación conservadora de las reglas de datos.

## Decisión
Zonas roja (`data/`, `work/`) y verde (`outputs/`, `submissions/`, `docs/wiki/`). Claude Code con API key de
la Console, permisos `deny` y hook sobre la zona roja, y `mva-guard` antes de leer o commitear la zona verde.

## Evidencia
- [Discusión #2 del Space](https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026/discussions/2)
- `docs/DATA_POLICY.md`

## Consecuencias
Los pasos sobre datos reales los corre siempre el humano (`make real-*`).
