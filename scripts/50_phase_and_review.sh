#!/usr/bin/env bash
# Fase 2 · Fase cis/trans de los candidatos (WhatsHap) + reporte IGV local.   ZONA ROJA
#
# Sin padres no hay fase por segregación: WhatsHap usa lecturas que cubren ambas
# variantes. Funciona si están a menos de ~longitud de inserto (cientos de pb en
# short-read). Si están lejos, la fase queda "unknown" y se declara en el write-up.
#
# Uso: scripts/50_phase_and_review.sh work/normalized.vcf.gz data/x.bam ref/GRCh38.fa
set -euo pipefail
VCF="${1:?vcf}"; BAM="${2:?bam/cram}"; REF="${3:?fasta}"
mkdir -p work/phase work/igv

# Regiones de los top-10 (de outputs/top_pairs.tsv), ±200 kb
python3 - <<'PY' > work/phase/regions.bed
import pandas as pd
t = pd.read_csv("outputs/top_pairs.tsv", sep="\t", dtype=str, keep_default_na=False)
for _, r in t.iterrows():
    ps = [int(p) for p in (r["pos_1"], r["pos_2"]) if p]
    print(f"{r['chrom_1']}\t{max(0, min(ps) - 200_000)}\t{max(ps) + 200_000}\t{r['gene']}")
PY

bcftools view -R work/phase/regions.bed "$VCF" -Oz -o work/phase/candidates_regions.vcf.gz
bcftools index -t work/phase/candidates_regions.vcf.gz
whatshap phase --reference "$REF" --indels -o work/phase/phased.vcf.gz \
    work/phase/candidates_regions.vcf.gz "$BAM"
bcftools index -t work/phase/phased.vcf.gz
whatshap stats work/phase/phased.vcf.gz > work/phase/stats.txt

# Cis/trans por par: solo es comparable si ambas variantes están en el mismo bloque (PS).
bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t[%GT]\t[%PS]\n' work/phase/phased.vcf.gz > work/phase/gt_ps.tsv
python3 - <<'PY'
import pandas as pd
g = pd.read_csv("work/phase/gt_ps.tsv", sep="\t", header=None, dtype=str,
                names=["chrom", "pos", "ref", "alt", "gt", "ps"]).set_index(["chrom", "pos", "ref", "alt"])
t = pd.read_csv("outputs/top_pairs.tsv", sep="\t", dtype=str, keep_default_na=False)
rows = []
for _, r in t[t["pos_2"] != ""].iterrows():
    k1 = (r["chrom_1"], r["pos_1"], r["ref_1"], r["alt_1"]); k2 = (r["chrom_2"], r["pos_2"], r["ref_2"], r["alt_2"])
    phase = "unknown"
    if k1 in g.index and k2 in g.index:
        a = g.loc[[k1]].iloc[0]; b = g.loc[[k2]].iloc[0]
        if "|" in a.gt and "|" in b.gt and a.ps not in (".", "") and a.ps == b.ps:
            phase = "cis" if a.gt.split("|").index("1") == b.gt.split("|").index("1") else "trans"
    rows.append(dict(gene=r["gene"], chrom_1=r["chrom_1"], pos_1=r["pos_1"],
                     chrom_2=r["chrom_2"], pos_2=r["pos_2"], phase=phase))
pd.DataFrame(rows).to_csv("outputs/phase_summary.tsv", sep="\t", index=False)
print(pd.DataFrame(rows)[["gene", "phase"]].to_string(index=False))
PY

# Reporte IGV autocontenido (contiene lecturas: ZONA ROJA, se borra al final)
python3 - <<'PY' > work/igv/sites.bed
import pandas as pd
t = pd.read_csv("outputs/top_pairs.tsv", sep="\t", dtype=str, keep_default_na=False)
for _, r in t.iterrows():
    for s in ("1", "2"):
        if r[f"pos_{s}"]:
            p = int(r[f"pos_{s}"]); print(f"{r[f'chrom_{s}']}\t{p-1}\t{p}\t{r['gene']}")
PY
create_report work/igv/sites.bed --fasta "$REF" --tracks "$BAM" --flanking 150 \
    --output work/igv/candidates_igv.html
echo "Fase: work/phase/phased.vcf.gz · IGV: work/igv/candidates_igv.html (revisión humana)"
echo "Siguiente: make prioritize PHASE=outputs/phase_summary.tsv"
