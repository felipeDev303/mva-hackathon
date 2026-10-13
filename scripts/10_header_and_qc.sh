#!/usr/bin/env bash
# Fase 0 · QC agregado y cabecera sin muestras.   ZONA ROJA → verde (solo agregados)
# Lo corre el humano. Uso: scripts/10_header_and_qc.sh data/<archivo>.vcf.gz
set -euo pipefail
VCF="${1:?uso: $0 data/x.vcf.gz}"
mkdir -p work outputs fixtures

# Cabecera sin columnas de muestra (-G): contigs, INFO, FORMAT, referencia.
bcftools view -h -G "$VCF" > work/header_nosamples.txt
# Copia apta para fixtures (no contiene genotipos ni el id de la muestra).
grep -v '^#CHROM' work/header_nosamples.txt > fixtures/header_nosamples.txt

bcftools stats -s - "$VCF" > work/bcftools_stats.txt
mva-qc work/bcftools_stats.txt --header work/header_nosamples.txt -o outputs/qc_summary.json > /dev/null

# Lista de muestras → config del guard (para que nunca aparezcan en outputs/)
bcftools query -l "$VCF" > work/sample_ids.txt
echo "QC listo: outputs/qc_summary.json  ($(wc -l < work/sample_ids.txt) muestra(s))"
echo "Agrega el/los id de work/sample_ids.txt a guard.sample_ids en config/config.yaml (no lo pegues en el chat)."
