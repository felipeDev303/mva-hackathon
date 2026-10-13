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
PRESET="${PRESET:-$EXOMISER_HOME/examples/preset-genome-analysis.yml}"
mkdir -p work/exomiser outputs

mva-exomiser-config --preset "$PRESET" --vcf "$VCF" -o work/exomiser-analysis.yml
( cd "$EXOMISER_HOME" && java -Xmx"${EXOMISER_MEM:-12g}" -jar "$JAR" analyse \
    --analysis "$OLDPWD/work/exomiser-analysis.yml" \
    --output-directory "$OLDPWD/work/exomiser" \
    --output-format HTML,TSV_GENE,TSV_VARIANT ) > work/exomiser/run.log 2>&1

GENES=$(ls work/exomiser/*genes.tsv | head -1)
mva-exomiser-summary "$GENES" -o outputs/exomiser_genes_top50.tsv
echo "Exomiser listo. HTML (zona roja): work/exomiser/  ·  resumen: outputs/exomiser_genes_top50.tsv"
