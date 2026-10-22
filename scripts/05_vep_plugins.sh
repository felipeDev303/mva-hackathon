#!/usr/bin/env bash
# Fase 1 · Datos de plugins de VEP 116 (una vez): módulos .pm, AlphaMissense y REVEL v1.3.
# SpliceAI: por defecto se usa scripts/06_spliceai_panel.sh (consulta dirigida a los genes del panel), porque
# el archivo genómico de Ensembl (28,6 GB) no es viable con conexiones lentas; SPLICEAI_FULL=1 lo descarga entero.
# Solo datos públicos; no toca data/ ni work/. Idempotente: salta lo ya hecho y verifica tamaños.
# Requiere el entorno conda activo (tabix, bgzip).  Uso: scripts/05_vep_plugins.sh [destino]
set -euo pipefail
DEST="${1:-$HOME/mva/ref/plugins}"; PLUGIN_DIR="${VEP_PLUGINS:-$HOME/.vep/Plugins}"
mkdir -p "$DEST"; cd "$DEST"
WGET=(wget --tries=0 --read-timeout=60 --waitretry=10 -nv)

# Descarga verificada: compara el tamaño local con el del servidor; si no calza, borra y baja de nuevo.
fetch() {
  local url=$1 out; out=$(basename "$url")
  local remote; remote=$(curl -sIL "$url" | grep -i '^content-length' | tail -1 | tr -dc 0-9)
  if [[ -f "$out" && -n "$remote" && $(stat -c %s "$out") -ne $remote ]]; then
    echo "  $out: tamaño distinto al del servidor ($(stat -c %s "$out") ≠ $remote), se baja de nuevo"; rm -f "$out" "$out.tbi"
  fi
  [[ -f "$out" ]] || "${WGET[@]}" -c "$url"
  [[ -z "$remote" || $(stat -c %s "$out") -eq $remote ]] || { echo "ERROR: $out incompleto" >&2; return 1; }
}

# Módulos de los plugins, misma release que VEP
if [[ ! -f "$PLUGIN_DIR/AlphaMissense.pm" ]]; then
  git clone --depth 1 -b release/116 https://github.com/Ensembl/VEP_plugins "$PLUGIN_DIR"
fi

# AlphaMissense (Cheng et al. 2023), ~0,6 GB; índice según la doc de AlphaMissense.pm
AM=AlphaMissense_hg38.tsv.gz
fetch "https://storage.googleapis.com/dm_alphamissense/$AM"
[[ -f "$AM.tbi" ]] || tabix -s 1 -b 2 -e 2 -f -S 1 "$AM"
echo "AlphaMissense listo"

# REVEL v1.3 (Ioannidis et al. 2016), ~0,7 GB; formato GRCh38 según la doc de REVEL.pm
REVEL_OUT=new_tabbed_revel_grch38.tsv.gz
if [[ ! -f "$REVEL_OUT.tbi" ]]; then
  fetch https://rothsj06.dmz.hpc.mssm.edu/revel-v1.3_all_chromosomes.zip
  unzip -o -q revel-v1.3_all_chromosomes.zip
  tr "," "\t" < revel_with_transcript_ids | sed '1s/.*/#&/' > tabbed_revel.tsv
  head -n1 tabbed_revel.tsv > revel_header
  grep -v '^#' tabbed_revel.tsv | awk '$3 != "."' | sort -S 4G -T . -k1,1 -k3,3n \
    | cat revel_header - | bgzip -c > "$REVEL_OUT"
  tabix -f -s 1 -b 3 -e 3 "$REVEL_OUT"
  rm -f revel_with_transcript_ids tabbed_revel.tsv revel_header
fi
echo "REVEL listo"

# SpliceAI genómico completo (opcional)
SAI=spliceai_scores.masked.snv.ensembl_mane_v1.4.grch38.vcf.gz
if [[ "${SPLICEAI_FULL:-0}" == 1 ]]; then
  B=https://ftp.ensembl.org/pub/data_files/homo_sapiens/GRCh38/variation_plugins
  fetch "$B/$SAI.tbi"; fetch "$B/$SAI"
  echo "SpliceAI completo listo"
fi

cat <<EOF
Agrega a ~/mva/env.sh:
export VEP_PLUGINS=$PLUGIN_DIR
export ALPHAMISSENSE=$DEST/$AM
export REVEL=$DEST/$REVEL_OUT
export SPLICEAI_SNV=$DEST/$( [[ "${SPLICEAI_FULL:-0}" == 1 ]] && echo "$SAI" || echo spliceai_panel.chr.vcf.gz )
EOF
