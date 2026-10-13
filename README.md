# MVA Hackathon 2026 · Track 1 — pipeline de priorización

Pipeline reproducible para proponer la(s) variante(s) causal(es) de un caso de
Mosaic Variegated Aneuploidy (MVA) a partir de WGS (VCF/BAM) y fenotipos HPO.
Hackathon: [Rare Disease, Real Kid](https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026).

> **Datos:** este repo **no** contiene datos del paciente. El dataset es gated
> (WCG IRB #20252010); se descarga localmente en `data/` y se borra 30 días
> después del cierre. Ver [`docs/DATA_POLICY.md`](docs/DATA_POLICY.md).

## Arquitectura: dos zonas

| Zona | Carpetas | Quién la lee |
|---|---|---|
| 🔴 Roja | `data/`, `work/` | solo el humano y los scripts locales |
| 🟢 Verde | `outputs/`, `submissions/`, `fixtures/`, código, docs | también el asistente LLM, tras `make guard` |

El asistente escribe código y lo prueba con datos **sintéticos** (`fixtures/`).
El humano corre los objetivos `make real-*`. `mva-guard` impide que a la zona
verde llegue algo con forma de genoma.

## Inicio rápido

```bash
# WSL2 / Linux
make setup && conda activate mva
make test                      # 23 tests con fixtures sintéticos
# editar config/config.yaml (rutas) y config/hpo_terms.txt (HPO del caso)
make real-qc                   # → outputs/qc_summary.json
make real-normalize real-annotate real-exomiser real-prioritize
make real-phase && make real-prioritize PHASE=outputs/phase_summary.tsv
make fetch-eval real-submission  # → submissions/track1_submission.csv validado
```

## Estructura

```
config/       config.yaml (todos los umbrales), hpo_terms.txt, en git
scripts/      NN_*.sh por fase (10 QC, 20 normalize, 30 VEP, 40 Exomiser, 50 fase/IGV, 90 borrado)
src/mva/      guard, fixtures, qc, exomiser, prioritize, submission (CLIs mva-*)
tests/        pytest contra fixtures sintéticos
fixtures/     datos sintéticos + cabecera sin muestras
docs/         METHODS (write-up), LITERATURE, DATA_POLICY
data/ work/   🔴 fuera de git
outputs/      🟢 agregados: qc_summary.json, funnel.json, genes_ranked.tsv, top_pairs.tsv, ...
submissions/  🟢 CSV de entrega
vendor/       evaluation.py oficial (descargado, fuera de git)
```

## Uso de LLM

Asistente: Claude Code con API key de la Anthropic Console (términos comerciales,
sin entrenamiento con datos del cliente). Ver `CLAUDE.md` y `docs/DATA_POLICY.md`.

## Licencia y cita

Código y resultados bajo CC BY 4.0. Agradecimiento obligatorio: ver `docs/METHODS.md`.
