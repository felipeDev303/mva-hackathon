#!/usr/bin/env bash
# Fase 1 · Anotación con Ensembl VEP 116 (offline) + tabla plana.   ZONA ROJA
#
# Requisitos (una vez):
#   vep_install -a cf -s homo_sapiens -y GRCh38 -c ~/.vep --CONVERT     # caché ~25 GB
#   Plugins opcionales (descarga sus archivos y exporta las rutas):
#     CADD_SNV / CADD_INDEL  (tabix de CADD v1.7 GRCh38)
#     REVEL                  (revel_grch38.tsv.gz)
#     SPLICEAI_SNV [/ SPLICEAI_INDEL] (scores precomputados, masked; el de indels es opcional)
#     ALPHAMISSENSE          (AlphaMissense_hg38.tsv.gz + .tbi)
#   Los módulos .pm de los plugins van en $VEP_PLUGINS (por defecto ~/.vep/Plugins, rama release/116).
#
# En WGS (~5 M variantes) tarda horas en una laptop: córrelo de noche.
# Uso: scripts/30_vep.sh work/normalized.vcf.gz work/vep.vcf.gz work/annotated.tsv
set -euo pipefail
IN="${1:-work/normalized.vcf.gz}"; OUT="${2:-work/vep.vcf.gz}"; TSV="${3:-work/annotated.tsv}"
CACHE="${VEP_CACHE:-$HOME/.vep}"; FORKS="${FORKS:-4}"; PLUGIN_DIR="${VEP_PLUGINS:-$HOME/.vep/Plugins}"

PLUGINS=()
[[ -n "${CADD_SNV:-}" && -n "${CADD_INDEL:-}" ]] && PLUGINS+=(--plugin "CADD,snv=${CADD_SNV},indels=${CADD_INDEL}")
[[ -n "${REVEL:-}" ]] && PLUGINS+=(--plugin "REVEL,file=${REVEL}")
if [[ -n "${SPLICEAI_SNV:-}" ]]; then
  # SpliceAI.pm exige snv e indel. Ensembl solo publica SNV: sin indels, se usa un VCF vacío (solo cabecera).
  SAI_INDEL="${SPLICEAI_INDEL:-}"
  if [[ -z "$SAI_INDEL" ]]; then
    SAI_INDEL=work/spliceai_indel_empty.vcf.gz
    bcftools view -h "$SPLICEAI_SNV" | bgzip -c > "$SAI_INDEL" && tabix -f -p vcf "$SAI_INDEL"
  fi
  PLUGINS+=(--plugin "SpliceAI,snv=${SPLICEAI_SNV},indel=${SAI_INDEL}")
fi
[[ -n "${ALPHAMISSENSE:-}" ]] && PLUGINS+=(--plugin "AlphaMissense,file=${ALPHAMISSENSE}")
echo "Plugins de VEP activos: $(( ${#PLUGINS[@]} / 2 )) ($(printf '%s\n' "${PLUGINS[@]}" | grep -v '^--plugin$' | cut -d, -f1 | paste -sd' '))"

vep --input_file "$IN" --output_file "$OUT" --vcf --compress_output bgzip \
    --offline --cache --dir_cache "$CACHE" --dir_plugins "$PLUGIN_DIR" --assembly GRCh38 --fork "$FORKS" \
    --everything --pick_allele_gene --canonical --mane \
    --af_gnomade --af_gnomadg --max_af --check_existing \
    "${PLUGINS[@]}" --force_overwrite --no_stats
bcftools index -t "$OUT"

# Tabla plana: una fila por variante y gen (transcrito canónico priorizado por --pick_allele_gene).
FIELDS='%CHROM\t%POS\t%REF\t%ALT\t%FILTER\t[%GT]\t%SYMBOL\t%Consequence\t%IMPACT\t%gnomADe_AF\t%gnomADg_AF\t%MAX_AF\t%CLIN_SIG\t%Existing_variation'
HDR='CHROM\tPOS\tREF\tALT\tFILTER\tGT\tSYMBOL\tConsequence\tIMPACT\tgnomADe_AF\tgnomADg_AF\tMAX_AF\tCLIN_SIG\tExisting_variation'
# Agrega columnas de plugins solo si existen en el CSQ
CSQ=$(bcftools +split-vep -l "$OUT" | cut -f2)
for f in CADD_PHRED REVEL am_pathogenicity SpliceAI_pred_DS_AG SpliceAI_pred_DS_AL SpliceAI_pred_DS_DG SpliceAI_pred_DS_DL; do
  if grep -qx "$f" <<<"$CSQ"; then FIELDS+="\t%$f"; HDR+="\t$f"; fi
done
{ printf "$HDR\n"; bcftools +split-vep "$OUT" -d -A tab -f "$FIELDS\n"; } > "$TSV"
echo "Anotado: $TSV ($(($(wc -l < "$TSV") - 1)) filas)"
