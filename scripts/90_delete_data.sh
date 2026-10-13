#!/usr/bin/env bash
# Cierre · Borrado de datos (plazo: 30 días tras el cierre del 24-oct-2026).
# Borra todo lo que porta el genoma del niño (lista DELETE de los organizadores).
# Conserva: outputs/, submissions/, config/, código, docs (lista KEEP).
# Uso: scripts/90_delete_data.sh            (pide confirmación)
set -euo pipefail
echo "Se borrará:"
echo "  - data/ (VCF, BAM/CRAM, FASTQ e índices)"
echo "  - work/ (normalizados, anotados, candidatos, Exomiser, fase, IGV)"
echo "  - ~/.cache/huggingface/hub/datasets--SageBio--mva-hackathon-2026-data"
echo "  - transcripciones locales de Claude Code de este proyecto (~/.claude/projects/*mva*)"
read -r -p "Escribe BORRAR para continuar: " ok
[[ "$ok" == "BORRAR" ]] || { echo "Cancelado."; exit 1; }

find data -mindepth 1 ! -name .gitkeep -exec rm -rf {} +
find work -mindepth 1 ! -name .gitkeep -exec rm -rf {} +
rm -rf "$HOME/.cache/huggingface/hub/datasets--SageBio--mva-hackathon-2026-data"
find "$HOME/.claude/projects" -maxdepth 1 -iname '*mva*' -exec rm -rf {} + 2>/dev/null || true

# Verificación: no debe quedar ningún archivo genómico fuera de fixtures/
LEFT=$(find . "$HOME" \( -name '*.vcf.gz' -o -name '*.bam' -o -name '*.cram' -o -name '*.fastq.gz' \) \
        -not -path './fixtures/*' 2>/dev/null | grep -i -E 'mva|REDACTED|REDACTED' || true)
if [[ -n "$LEFT" ]]; then echo "ATENCIÓN, quedan archivos:"; echo "$LEFT"; exit 1; fi
date -u +"Borrado completado %Y-%m-%dT%H:%MZ" | tee docs/DELETION_LOG.txt
echo "Ahora envía la confirmación a RarediseaserealkidMVAhackathon2026@synapse.org (plantilla en docs/DATA_POLICY.md)."
