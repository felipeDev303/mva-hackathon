# CLAUDE.md — reglas para el asistente en este repo

Este repo analiza el genoma de un niño real (MVA Hackathon 2026, dataset gated, IRB WCG #20252010).
El asistente escribe código; los datos del paciente nunca entran al contexto.

## Frontera de datos (no negociable)
- **Zona roja — no leer, no listar, no buscar, no editar:** `data/`, `work/`, cualquier `.vcf/.vcf.gz/.bam/.cram/.fastq`
  fuera de `fixtures/`. Un hook (`.claude/hooks/data_boundary.py`) lo bloquea; no intentes rodearlo.
- **Zona verde — sí puedes leer:** `outputs/` (solo después de que `make guard` pase), `fixtures/`,
  `config/`, `src/`, `tests/`, `docs/`.
- **No corras** objetivos sobre datos reales (`make real-*`). Escribe el código, pruébalo con `make test`
  y pide al humano que lo corra.
- Si el humano pega filas de variantes o genotipos en el chat, recuérdale la política y no las repitas.

## Contrato de los scripts
1. Todo script que lea zona roja escribe detalle por variante en `work/` y solo agregados en `outputs/`.
2. Nada imprime filas de variantes ni genotipos a stdout/stderr (solo conteos, rutas y resúmenes).
3. `outputs/` admite como máximo 50 filas a nivel variante por archivo y ninguna columna GT/AD/DP/GQ/PL.
4. Todo umbral vive en `config/config.yaml`; nada hardcodeado.
5. Cada módulo nuevo trae test en `tests/` contra `fixtures/`.

## Convenciones de código
- Python 3.11, paquete en `src/mva/`, CLI con argparse, entrypoints en `pyproject.toml` (`mva-*`).
- Shell en `scripts/NN_nombre.sh` con `set -euo pipefail`, numerados por fase.
- Tablas: TSV con cabecera; JSON para resúmenes. Coordenadas GRCh38 con prefijo `chr`.
- Mensajes y docs en español; nombres de código en inglés.
- Commits: `tipo(ámbito): mensaje` (feat, fix, test, docs, chore).

## Comandos
- `make test` — tests con fixtures sintéticos (seguro para el asistente)
- `make fixtures` — regenera fixtures
- `make guard` — valida `outputs/`
