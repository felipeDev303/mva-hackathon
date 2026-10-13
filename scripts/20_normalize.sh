#!/usr/bin/env bash
# Fase 1 · Normalización.   ZONA ROJA
# - divide multialélicos, alinea a la izquierda contra la referencia
# - conserva PASS y aplica umbrales mínimos de GQ/DP si existen en FORMAT
# Uso: scripts/20_normalize.sh data/x.vcf.gz ref/GRCh38.fa work/normalized.vcf.gz [min_gq] [min_dp]
set -euo pipefail
IN="${1:?vcf}"; REF="${2:?fasta}"; OUT="${3:-work/normalized.vcf.gz}"
MIN_GQ="${4:-20}"; MIN_DP="${5:-8}"
THREADS="${THREADS:-4}"

HDR=$(bcftools view -h "$IN")
EXPR=()
grep -q '##FORMAT=<ID=GQ,' <<<"$HDR" && EXPR+=("FMT/GQ<${MIN_GQ}")
grep -q '##FORMAT=<ID=DP,' <<<"$HDR" && EXPR+=("FMT/DP<${MIN_DP}")
EXCL=$(IFS='|'; echo "${EXPR[*]:-}")

bcftools norm --threads "$THREADS" -m -both -f "$REF" --check-ref w "$IN" -Ou \
  | bcftools view --threads "$THREADS" -f PASS,. ${EXCL:+-e "$EXCL"} -Ou \
  | bcftools view --threads "$THREADS" -i 'GT="alt"' -Oz -o "$OUT"
bcftools index -t "$OUT"
echo "Normalizado: $OUT  ($(bcftools index -n "$OUT") registros)"
