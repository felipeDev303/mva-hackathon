#!/usr/bin/env bash
# Cierre · Borrado de datos (plazo: 30 días tras el cierre del 24-oct-2026 → antes del 23-nov-2026).
# Borra todo lo que porta el genoma del niño (lista DELETE de los organizadores):
#   - los archivos REALES del dataset (data/ solo tiene enlaces simbólicos: se siguen hasta el destino)
#   - work/ (normalizados, anotados, candidatos, Exomiser, fase, IGV) y cachés de Hugging Face del dataset
#   - transcripciones locales de Claude Code de este proyecto en WSL (las de Windows se borran aparte)
#   - config/local.yaml (rutas a los datos e id de la muestra), al final
# Con REFS=1 borra además los datos públicos de referencia (caché de VEP, Exomiser, GRCh38, plugins).
# Conserva: outputs/, submissions/, config/, código y docs (lista KEEP).
# Uso: scripts/90_delete_data.sh        ·        REFS=1 scripts/90_delete_data.sh
set -euo pipefail
cd "$(dirname "$0")/.."
DATA_HOME="${DATA_HOME:-$HOME/mva/data}"

# Identificadores a verificar al final: se leen de la config local (nunca escritos en el repo)
mapfile -t IDS < <(python3 -c "
import yaml, pathlib
p = pathlib.Path('config/local.yaml')
d = yaml.safe_load(p.read_text()) if p.exists() else {}
ids = (d.get('guard') or {}).get('sample_ids') or []
raw = ((d.get('paths') or {}).get('raw_vcf') or '').split('/')[-1]
print('\n'.join([*ids, raw] if raw else ids))")

# Destinos reales de los enlaces de data/
mapfile -t TARGETS < <(find data -mindepth 1 -maxdepth 1 -type l -exec readlink -f {} \; | sort -u)

echo "Se borrará:"
echo "  - $DATA_HOME y los destinos de los enlaces de data/ (${#TARGETS[@]})"
echo "  - data/ y work/ del repo (excepto .gitkeep)"
echo "  - cachés de Hugging Face del dataset"
echo "  - transcripciones de Claude Code de proyectos 'mva' en WSL (~/.claude/projects)"
[[ "${REFS:-0}" == 1 ]] && echo "  - REFS=1: ~/.vep, ~/mva/exomiser, ~/mva/ref (datos públicos)"
echo "  - config/local.yaml (al final)"
read -r -p "Escribe BORRAR para continuar: " ok
[[ "$ok" == "BORRAR" ]] || { echo "Cancelado."; exit 1; }

for t in "${TARGETS[@]}"; do rm -rf -- "$t"; done
rm -rf -- "$DATA_HOME"
find data -mindepth 1 ! -name .gitkeep -exec rm -rf {} +
find work -mindepth 1 ! -name .gitkeep -exec rm -rf {} +
rm -rf "$HOME"/.cache/huggingface/hub/datasets--* "$HOME"/.cache/huggingface/datasets
find "$HOME/.claude/projects" -maxdepth 1 -iname '*mva*' -exec rm -rf {} + 2>/dev/null || true
if [[ "${REFS:-0}" == 1 ]]; then rm -rf "$HOME/.vep" "$HOME/mva/exomiser" "$HOME/mva/ref"; fi

# Verificación 1: ningún archivo genómico fuera de fixtures/ (y de las referencias si se conservan)
G='.*\.(vcf|vcf\.gz|bcf|bam|bai|cram|crai|fastq|fastq\.gz|fq|fq\.gz|ora|gvcf\.gz)$'
LEFT=$(find "$HOME" -xdev -type f -regextype posix-extended -regex "$G" -not -path '*/fixtures/*' \
         -not -path '*/miniforge3/*' -not -path '*/.vep/*' -not -path '*/mva/ref/*' -not -path '*/mva/exomiser/*' \
         2>/dev/null || true)
# Verificación 2: el id de la muestra y el nombre del VCF no aparecen en el home (fuera de .git y miniforge)
HITS=""
for s in "${IDS[@]}"; do
  [[ -n "$s" ]] || continue
  h=$(grep -rIl --exclude-dir=.git --exclude-dir=miniforge3 -F -- "$s" "$HOME" 2>/dev/null | grep -v 'config/local.yaml$' || true)
  [[ -n "$h" ]] && HITS+="$h"$'\n'
done
if [[ -n "$LEFT" || -n "$HITS" ]]; then
  echo "ATENCIÓN: quedan $(grep -c . <<<"$LEFT") archivo(s) genómico(s) y $(grep -c . <<<"$HITS") archivo(s) con identificadores."
  echo "Revísalos con cuidado (no los pegues en un chat)."; exit 1
fi
rm -f config/local.yaml
date -u +"Borrado completado %Y-%m-%dT%H:%MZ (REFS=${REFS:-0})" | tee docs/DELETION_LOG.txt
echo "Siguiente: borrar las transcripciones de Claude Code en Windows y enviar la confirmación a cnb@sagebase.org."
