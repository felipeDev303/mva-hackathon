#!/usr/bin/env bash
# Fase 1 · Exomiser 15.x (fenotipo HPO + variantes).   ZONA ROJA → verde (top genes)
#
# Instalación (una vez), ver https://exomiser.readthedocs.io :
#   - descarga exomiser-cli-15.1.0-distribution.zip y descomprímelo en $EXOMISER_HOME
#   - descarga los datos <release>_hg38.zip y <release>_phenotype.zip (release 2512 o posterior)
#     y configura application.properties (exomiser.data-directory, exomiser.hg38.data-version,
#     exomiser.phenotype.data-version)
# Requiere Java 21.  Uso: scripts/40_exomiser.sh work/normalized.vcf.gz
set -euo pipefail
VCF="${1:-work/normalized.vcf.gz}"
: "${EXOMISER_HOME:?exporta EXOMISER_HOME}"
JAR=$(ls "$EXOMISER_HOME"/exomiser-cli-*.jar | head -1)
PRESET=$(realpath "${PRESET:-config/exomiser-genome-analysis.yml}")
ASSEMBLY=$(python3 -c "import yaml;print(yaml.safe_load(open('config/config.yaml'))['assembly'])")
mkdir -p work/exomiser outputs

# Exomiser 15 pide muestra (phenopacket con HPO), VCF y análisis por separado.
# El id del phenopacket debe ser el de la muestra del VCF; queda solo en work/ y nunca se imprime.
VCF_SAMPLE=$(bcftools query -l "$VCF" | head -1)
mva-exomiser-config -o work/exomiser-sample.yml --proband-id "$VCF_SAMPLE"
SAMPLE=$(realpath work/exomiser-sample.yml); VCF_ABS=$(realpath "$VCF"); OUTDIR=$(realpath work/exomiser)
if ! ( cd "$EXOMISER_HOME" && java -Xmx"${EXOMISER_MEM:-12g}" -jar "$JAR" analyse \
    --sample "$SAMPLE" --vcf "$VCF_ABS" --assembly "$ASSEMBLY" --analysis "$PRESET" \
    --output-directory "$OUTDIR" --output-filename exomiser \
    --output-format HTML,TSV_GENE,TSV_VARIANT ) > work/exomiser/run.log 2>&1; then
  echo "Exomiser falló. Errores de work/exomiser/run.log (sin coordenadas ni id de muestra):" >&2
  grep -E ' ERROR |Caused by' work/exomiser/run.log | sed "s/${VCF_SAMPLE}/<muestra>/g" \
    | grep -vE 'chr[0-9XYM]+[-:_ ]+[0-9]{4,}|\b[0-9XYM]{1,2}-[0-9]{4,}-[ACGTN]+' | cut -c1-300 | tail -6 >&2
  exit 1
fi

GENES=$(ls work/exomiser/*genes.tsv | head -1)
mva-exomiser-summary "$GENES" -o outputs/exomiser_genes_top50.tsv
echo "Exomiser listo. HTML (zona roja): work/exomiser/  ·  resumen: outputs/exomiser_genes_top50.tsv"
