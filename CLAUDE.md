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

## Wiki (`docs/wiki/`, vault de Obsidian)
- Es **zona verde**: puedes leerla y escribirla, pero nada que no pasaría `make guard` (sin filas de `work/`,
  sin genotipos, sin el id de la muestra, ≤ 10 variantes nombradas, sin capturas de IGV).
- Carpetas: `diario/`, `corridas/`, `decisiones/` (ADR-NNN), `envios/` (SUB-N), `genes/`, `literatura/`, `plan/`.
- Toda nota lleva el frontmatter de su plantilla en `plantillas/` (lo consume el tablero de Dataview).
- Crea notas con la CLI, no a mano: `mva-wiki day`, `mva-wiki run real-<paso>`, `mva-wiki adr "título"`,
  `mva-wiki sub`. La CLI lee solo `outputs/` y `submissions/` y pasa el guard antes de escribir.
- Tras una corrida que el humano te avise: completa "Qué cambió" e "Interpretación" de la nota de corrida a
  partir de `outputs/`, enlaza el ADR que corresponda y actualiza `00-inicio.md` (fase y próximos pasos).
- Cambiar un umbral o peso en `config.yaml` exige un ADR nuevo o actualizado.
- Notas de literatura: solo fuentes públicas, con DOI o enlace; nunca inventes una cita.

## Comandos
- `make test` — tests con fixtures sintéticos (seguro para el asistente)
- `make fixtures` — regenera fixtures
- `make guard` — valida `outputs/`, `submissions/` y `docs/wiki/`
- `make wiki-day` · `make wiki-adr T="título"` · `make wiki-sub` — notas de la wiki
