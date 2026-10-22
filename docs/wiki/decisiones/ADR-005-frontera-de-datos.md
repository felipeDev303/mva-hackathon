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

## Actualización 22-oct-2026
Los organizadores corrigieron su guía en la Discusión #2. Las cuentas de **consumo** (Claude Free/Pro, ChatGPT Plus)
están permitidas con información específica o derivada del paciente si se cumplen dos condiciones:

1. el entrenamiento de modelos está desactivado en la cuenta;
2. no se da feedback (👍/👎) y el contenido no queda marcado para revisión de seguridad.

Configuración usada en este proyecto: **Claude Pro/Max (Claude Code, extensión de VS Code), modelo Claude Opus 5.5,
entrenamiento desactivado desde antes del proyecto, sin feedback.** La frontera de datos no cambia: el asistente no ve
genotipos ni `work/`. Los pasos `make real-*` siguen siendo del humano.
