# MVA Hackathon 2026 · Track 1 — pipeline de priorización de variantes

> **Summary (EN).** Reproducible pipeline that proposed the causal variants for a child with mosaic variegated
> aneuploidy (MVA) from a single-sample WGS VCF and HPO terms. Top hypothesis: **compound heterozygous BUB1B
> c.2210T>G p.(Leu737\*) + c.3006T>G p.(Asn1002Lys)** (MVA1, autosomal recessive), ranked first with and without a gene
> prior and confirmed by the automated evaluation (**100 rank points, F-max 1.000**).
> Methods report: [`docs/felipemoralesdev_track1_report.md`](docs/felipemoralesdev_track1_report.md).

Hackathon: [Rare Disease, Real Kid](https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026) ·
Código y resultados bajo **CC BY 4.0**.

> **Datos:** este repo **no** contiene datos del paciente. El dataset es de acceso controlado (WCG IRB #20252010); se
> descarga localmente en `data/` y se borra 30 días después del cierre. Las rutas a los datos y el id de la muestra van en
> `config/local.yaml`, que git ignora. Ver [`docs/DATA_POLICY.md`](docs/DATA_POLICY.md).

## Resultado

| | |
|---|---|
| Hipótesis | BUB1B (MVA1, OMIM 257300), compuesto heterocigoto, fase desconocida |
| Variantes | c.2210T>G p.(Leu737\*), nonsense, exón 17/23 · c.3006T>G p.(Asn1002Lys), missense, dominio quinasa |
| Ranking propio | #1 con prior de genes y #1 **sin** prior |
| Exomiser 15.1 (sin prior) | BUB1B #1 (AD) y #2 (AR); igual con 7 u 8 HPO |
| Evaluación automática | 100 rank points · F-max 1,000 |

Detalle, ACMG/AMP, limitaciones y uso del LLM en el [informe de métodos](docs/felipemoralesdev_track1_report.md).

## Arquitectura: dos zonas

| Zona | Carpetas | Quién la lee |
|---|---|---|
| 🔴 Roja | `data/`, `work/` | solo el humano y los scripts locales |
| 🟢 Verde | `outputs/`, `submissions/`, `docs/wiki/`, `fixtures/`, código, docs | también el asistente LLM, tras `make guard` |

El asistente escribe código y lo prueba con datos **sintéticos** (`fixtures/`). El humano corre los objetivos
`make real-*`. `mva-guard` (y un pre-commit) impiden que llegue a la zona verde o a git algo con forma de genoma o el id
de la muestra.

## Reproducir

```bash
# WSL2 / Linux, entorno conda
make setup && conda activate mva
make test                                   # 42 tests con fixtures sintéticos

# Configuración local (fuera de git): rutas y id de la muestra
cat > config/local.yaml <<'EOF'
paths:
  raw_vcf: data/<archivo>.vcf.gz
guard:
  sample_ids: [<id de la muestra>]
EOF
# HPO del caso en config/hpo_terms.txt (7 del probando; ver ADR-008)

# Datos públicos de una vez: caché VEP 116, referencia GRCh38, Exomiser 15.1.0 + datos 2512 (ver docs/wiki)
scripts/05_vep_plugins.sh                   # AlphaMissense, REVEL y módulos de plugins de VEP
scripts/06_spliceai_panel.sh                # SpliceAI dirigido a los 29 genes del panel
source ~/mva/env.sh                         # VEP_CACHE, EXOMISER_HOME, ALPHAMISSENSE, REVEL, SPLICEAI_SNV

make real-qc real-normalize
FORKS=8 make real-annotate                  # horas
make real-exomiser real-prioritize
make fetch-eval
make real-submission EPCR=config/epcr_overrides.csv
```

`make real-phase` no aplica: el dataset no trae BAM/CRAM ni datos de los padres.

## Decisiones (ADR)

Cada umbral, peso o cambio de método tiene su ADR en [`docs/wiki/decisiones/`](docs/wiki/decisiones/), y cada corrida su
nota en [`docs/wiki/corridas/`](docs/wiki/corridas/), con su commit.

| ADR | Decisión |
|---|---|
| 001–004 | Modelo recesivo, umbrales de frecuencia, peso de Exomiser, rescate de variantes conocidas |
| 005 | Frontera de datos y uso del LLM |
| 006 | Wiki dentro del repo |
| 007 | Nomenclatura `chr` y referencia de normalización |
| 008 | 7 HPO del probando; HP:0200067 como sensibilidad |
| 009 | Exomiser 15: phenopacket y preset de genoma sin REMM |
| 010 | Predictores de VEP y pesos solo con predictores presentes |
| 011 | EPCR de la hipótesis principal |

## Estructura

```
config/       config.yaml (umbrales y pesos), hpo_terms.txt, exomiser-genome-analysis.yml, epcr_overrides.csv
              local.yaml (fuera de git: rutas a los datos e id de la muestra)
scripts/      05/06 datos de plugins · 10 QC · 20 normalización · 30 VEP · 40 Exomiser · 50 fase/IGV · 90 borrado
src/mva/      guard, fixtures, qc, exomiser, prioritize, submission, wiki (CLIs mva-*)
tests/        pytest contra fixtures sintéticos
fixtures/     datos sintéticos + cabecera estructural del VCF real (sin muestras ni metadatos)
docs/         informe de métodos, METHODS (plantilla), LITERATURE, DATA_POLICY, wiki/ (vault de Obsidian)
data/ work/   🔴 fuera de git
outputs/      🟢 agregados: qc_summary.json, funnel.json, genes_ranked.tsv, top_pairs.tsv, exomiser_genes_top50*.tsv
submissions/  🟢 CSV de entrega
```

## Wiki de seguimiento

`docs/wiki/` es un vault de Obsidian versionado con el repo (zona verde). Requiere el plugin comunitario **Dataview** para
el tablero (`plan/tablero.md`). Cada `make real-*` deja su nota en `corridas/`; `make wiki-adr T="..."` y `make wiki-sub`
crean decisiones y notas de envío.

## Uso de LLM

Claude Code (extensión de VS Code), modelo Claude Opus 5.5, suscripción Claude Pro/Max **con el entrenamiento de modelos
desactivado y sin feedback**, conforme a la guía actualizada de los organizadores (Discusión #2 del Space). El asistente
no accedió a genotipos ni a `work/`. Ver ADR-005 y la sección 9 del informe.

## Agradecimiento

"This work was made possible through the Hackathon, organized by Sage Bionetworks in partnership with the MVA Society,
Hugging Face, and BEACON (The Benchmarking, Evaluation, and Assessment Consortium for Science), with prize sponsorship
from AWS and Anthropic. We are deeply grateful to the child and their family who generously contributed their data and
their story to advance research into this rare disease. We acknowledge their trust in making this Hackathon possible."
