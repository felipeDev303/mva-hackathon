#!/usr/bin/env bash
# Fase 1 · Anotación con Ensembl VEP 116 (offline) + tabla plana.   ZONA ROJA
#
# Requisitos (una vez):
#   vep_install -a cf -s homo_sapiens -y GRCh38 -c ~/.vep --CONVERT     # caché ~25 GB
#   Plugins opcionales (descarga sus archivos y exporta las rutas):
#     CADD_SNV / CADD_INDEL  (tabix de CADD v1.7 GRCh38)
#     REVEL                  (revel_grch38.tsv.gz)
#     SPLICEAI_SNV / SPLICEAI_INDEL (scores precomputados, masked)
#
# En WGS (~5 M variantes) tarda horas en una laptop: córrelo de noche.
# Uso: scripts/30_vep.sh work/normalized.vcf.gz work/vep.vcf.gz work/annotated.tsv
set -euo pipefail
IN="${1:-work/normalized.vcf.gz}"; OUT="${2:-work/vep.vcf.gz}"; TSV="${3:-work/annotated.tsv}"
CACHE="${VEP_CACHE:-$HOME/.vep}"; FORKS="${FORKS:-4}"

PLUGINS=()
[[ -n "${CADD_SNV:-}" && -n "${CADD_INDEL:-}" ]] && PLUGINS+=(--plugin "CADD,snv=${CADD_SNV},indels=${CADD_INDEL}")
[[ -n "${REVEL:-}" ]] && PLUGINS+=(--plugin "REVEL,file=${REVEL}")
[[ -n "${SPLICEAI_SNV:-}" && -n "${SPLICEAI_INDEL:-}" ]] && PLUGINS+=(--plugin "SpliceAI,snv=${SPLICEAI_SNV},indel=${SPLICEAI_INDEL}")

vep --input_file "$IN" --output_file "$OUT" --vcf --compress_output bgzip \
    --offline --cache --dir_cache "$CACHE" --assembly GRCh38 --fork "$FORKS" \
    --everything --pick_allele_gene --canonical --mane \
    --af_gnomade --af_gnomadg --max_af --check_existing \
    "${PLUGINS[@]}" --force_overwrite --no_stats
bcftools index -t "$OUT"

# Tabla plana: una fila por variante y gen (transcrito canónico priorizado por --pick_allele_gene).
FIELDS='%CHROM\t%POS\t%REF\t%ALT\t%FILTER\t[%GT]\t%SYMBOL\t%Consequence\t%IMPACT\t%gnomADe_AF\t%gnomADg_AF\t%MAX_AF\t%CLIN_SIG\t%Existing_variation'
HDR='CHROM\tPOS\tREF\tALT\tFILTER\tGT\tSYMBOL\tConsequence\tIMPACT\tgnomADe_AF\tgnomADg_AF\tMAX_AF\tCLIN_SIG\tExisting_variation'
# Agrega columnas de plugins solo si existen en el CSQ
CSQ=$(bcftools +split-vep -l "$OUT" | cut -f2)
for f in CADD_PHRED REVEL SpliceAI_pred_DS_AG SpliceAI_pred_DS_AL SpliceAI_pred_DS_DG SpliceAI_pred_DS_DL; do
  if grep -qx "$f" <<<"$CSQ"; then FIELDS+="\t%$f"; HDR+="\t$f"; fi
done
{ printf "$HDR\n"; bcftools +split-vep "$OUT" -d -A tab -f "$FIELDS\n"; } > "$TSV"
echo "Anotado: $TSV ($(($(wc -l < "$TSV") - 1)) filas)"
