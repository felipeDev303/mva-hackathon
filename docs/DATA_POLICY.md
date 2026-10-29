# Política de datos (resumen operativo)

Fuente: Official Rules del Space y respuesta del Chief Privacy & Compliance Officer de Sage
en la [discusión #2](https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026/discussions/2).

## Prohibido
- Redistribuir el dataset o darle acceso a terceros (personas o servicios que adquieran derechos).
- Intentar recontactar a la familia o a la MVA Society.
- Retener datos más de 30 días después del cierre (24-oct-2026 23:59 UTC → borrar antes del ~23-nov-2026).

## LLMs: test Processor vs. Recipient
Permitido solo si el proveedor **no entrena** con inputs/outputs ni adquiere derechos, y la
retención es limitada en tiempo y propósito. No calificar respuestas.

**Guía actualizada de los organizadores (discusión #2, fines de sep-2026):** también se permiten
cuentas de **consumo** (Claude Free/Pro, ChatGPT Plus) con información derivada del paciente, si
el entrenamiento de modelos está **desactivado** en la cuenta y **no se da feedback** (👍/👎) ni hay
contenido marcado para revisión de seguridad. Antes de esa corrección se exigía tier Business/API.

Línea usada en el write-up:
> Anthropic Claude Pro/Max subscription (Claude Code, VS Code extension), model Claude Opus 5.5;
> model-training opt-out enabled for the whole project; no feedback (ratings) provided. The
> assistant accessed code, synthetic fixtures and guard-validated aggregates; genotype-level data
> never left the local machine.

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
> Third-party services used: <proveedor, plan y configuración; p. ej. Claude Pro/Max with
> model-training opt-out, no feedback provided>.
> Retained: submission, HPO terms, gene-level rankings, code and report, per the organizers' KEEP list.

Para generar el borrado: `scripts/90_delete_data.sh` (con `REFS=1` borra también las referencias
públicas). El script lee los identificadores de `config/local.yaml` para verificar que no quede nada
y deja la fecha en `docs/DELETION_LOG.txt`.
