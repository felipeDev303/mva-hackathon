#!/usr/bin/env bash
# Fase 1 · SpliceAI dirigido a los genes del panel (MVA + punto de control mitótico de config.yaml).
# El archivo genómico de Ensembl (28,6 GB) no es viable de bajar entero: se consulta a distancia con tabix
# solo en las regiones de esos genes (± FLANK pb). Datos públicos; no toca data/ ni work/.
# Requiere el entorno conda activo (tabix, bgzip, bcftools).
# Uso: scripts/06_spliceai_panel.sh [destino]   → spliceai_panel.vcf.gz (sin chr) y spliceai_panel.chr.vcf.gz
set -euo pipefail
DEST="${1:-$HOME/mva/ref/plugins}"; FLANK="${FLANK:-5000}"
URL=https://ftp.ensembl.org/pub/data_files/homo_sapiens/GRCh38/variation_plugins/spliceai_scores.masked.snv.ensembl_mane_v1.4.grch38.vcf.gz
mkdir -p "$DEST"; TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# Genes del panel desde la config (mva_established + mitotic_checkpoint)
GENES=$(python3 -c "
from mva import load_config
p = load_config()['gene_prior']['panels']
print(' '.join(sorted({g for panel in p.values() for g in panel['genes']})))")
echo "Genes del panel: $(wc -w <<<"$GENES")"

# Coordenadas GRCh38 de cada gen (Ensembl REST, público), con flancos
: > "$TMP/panel.bed"
for g in $GENES; do
  j=$(curl -fsS --retry 8 --retry-delay 5 --retry-all-errors \
      "https://rest.ensembl.org/lookup/symbol/homo_sapiens/$g?content-type=application/json" 2>/dev/null || true)
  python3 -c "
import json, sys
try: d = json.loads(sys.argv[1])
except Exception: sys.exit('sin coordenadas: $g')
print(f\"{d['seq_region_name']}\t{max(0, d['start'] - 1 - $FLANK)}\t{d['end'] + $FLANK}\t$g\")" "$j" >> "$TMP/panel.bed" \
    || echo "  ⚠ $g: no encontrado en Ensembl REST"
done
N_GENES=$(wc -w <<<"$GENES"); N_BED=$(wc -l < "$TMP/panel.bed")
if (( N_BED < N_GENES )); then
  echo "ERROR: faltan $((N_GENES - N_BED)) gen(es) del panel (Ensembl REST inestable). Vuelve a correr el script." >&2
  exit 1
fi
sort -k1,1V -k2,2n "$TMP/panel.bed" > "$TMP/panel.sorted.bed"
echo "Regiones: $(wc -l < "$TMP/panel.sorted.bed") · $(awk '{s+=$3-$2} END{printf "%.1f", s/1e6}' "$TMP/panel.sorted.bed") Mb"

# Consulta remota solo de esas regiones
cd "$TMP"
{ tabix -H "$URL"; tabix -R panel.sorted.bed "$URL"; } | bgzip -c > spliceai_panel.vcf.gz
bcftools sort -Oz -o "$DEST/spliceai_panel.vcf.gz" spliceai_panel.vcf.gz 2>/dev/null
tabix -f -p vcf "$DEST/spliceai_panel.vcf.gz"

# Copia con prefijo chr (nuestro VCF usa chr); el piloto de VEP decide cuál lee bien el plugin
for c in $(seq 1 22) X Y MT; do printf '%s\tchr%s\n' "$c" "${c/MT/M}"; done > chrmap.txt
bcftools annotate --rename-chrs chrmap.txt -Oz -o "$DEST/spliceai_panel.chr.vcf.gz" "$DEST/spliceai_panel.vcf.gz"
tabix -f -p vcf "$DEST/spliceai_panel.chr.vcf.gz"
cp panel.sorted.bed "$DEST/spliceai_panel.bed"

echo "SpliceAI del panel: $(bcftools index -n "$DEST/spliceai_panel.vcf.gz") SNV con score → $DEST/spliceai_panel{,.chr}.vcf.gz"
echo "Para VEP: export SPLICEAI_SNV=$DEST/spliceai_panel.chr.vcf.gz   (o la versión sin chr, según el piloto)"
