# Política de datos (resumen operativo)

Fuente: Official Rules del Space y respuesta del Chief Privacy & Compliance Officer de Sage
en la [discusión #2](https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026/discussions/2).

## Prohibido
- Redistribuir el dataset o darle acceso a terceros (personas o servicios que adquieran derechos).
- Intentar recontactar a la familia o a la MVA Society.
- Retener datos más de 30 días después del cierre (24-oct-2026 23:59 UTC → borrar antes del ~23-nov-2026).

## LLMs: test Processor vs. Recipient
Permitido solo si el proveedor **no entrena** con inputs/outputs ni adquiere derechos, y la
retención es limitada en tiempo y propósito. Para datos del paciente: **tier Business/API**,
no suscripciones de consumo (aunque tengan el entrenamiento desactivado). No calificar respuestas.

Línea para el write-up (rellenar):
> LLM use: Anthropic API (Claude Code authenticated with a Console API key), model <MODELO>,
> Commercial Terms, no training on customer content. The assistant only accessed code,
> synthetic fixtures and aggregate outputs validated by `mva-guard`; genotype-level data never
> left the local machine.

## DELETE vs. KEEP
| DELETE (porta el genoma) | KEEP (hallazgos) |
|---|---|
| VCF, BAM, CRAM, FASTQ, índices y cualquier subconjunto o reformateo | lista de candidatas (la entrega) |
| `work/`: normalizados, anotados, candidatos con GT, Exomiser, fase, IGV | términos HPO |
| caché de HF del dataset | rankings de genes/vías, mecanismo, fármacos |
| prompts/transcripciones locales con bloques de variantes (`~/.claude/projects/...`) | código, informe, pitch, leaderboard |
| modelos/embeddings entrenados sobre los datos crudos | `outputs/` (validado por guard) |

## Confirmación de borrado (plantilla)
Para: cnb@sagebase.org
Asunto: MVA Hackathon 2026 – data deletion confirmation – <HF username>

> I confirm that on <fecha> I deleted all hackathon data (VCF/BAM/CRAM/FASTQ, indices, derived
> genotype-level tables, caches and local logs) from all systems I control: <laptop, WSL2>.
> Third-party services used: Anthropic API (Commercial Terms, no training on customer content).
> Retained: submission, HPO terms, gene-level rankings, code and report, per the organizers' KEEP list.
