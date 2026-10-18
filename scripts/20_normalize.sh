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

# Cromosomas primarios con prefijo "chr": el Space exige chr y la referencia de análisis lo usa.
# El VCF del dataset viene sin prefijo (1, 2, …, MT); si ya lo trae, el mapa no cambia nada.
CHR_MAP=$(mktemp); trap 'rm -f "$CHR_MAP"' EXIT
{ for c in {1..22} X Y; do printf '%s\tchr%s\n' "$c" "$c"; done; printf 'MT\tchrM\nM\tchrM\n'; } > "$CHR_MAP"
PRIMARY=$(printf 'chr%s,' {1..22} X Y M); PRIMARY=${PRIMARY%,}

bcftools annotate --threads "$THREADS" --rename-chrs "$CHR_MAP" "$IN" -Ou \
  | bcftools view --threads "$THREADS" -t "$PRIMARY" -Ou \
  | bcftools norm --threads "$THREADS" -m -both -f "$REF" --check-ref w -Ou \
  | bcftools view --threads "$THREADS" -f PASS,. ${EXCL:+-e "$EXCL"} -Ou \
  | bcftools view --threads "$THREADS" -i 'GT="alt"' -Oz -o "$OUT"
bcftools index -t "$OUT"
echo "Normalizado: $OUT  ($(bcftools index -n "$OUT") registros)"
