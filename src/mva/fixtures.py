"""Generador de datos SINTÉTICOS para desarrollar y testear sin tocar el paciente.

Produce dos archivos en fixtures/:
  * synthetic.vcf          VCF con variantes inventadas (para probar comandos bcftools)
  * synthetic_annotated.tsv  tabla con el mismo esquema que `bcftools +split-vep`
                           (para probar prioritize.py)

Planta escenarios conocidos para que los tests verifiquen que el pipeline los
recupera: un par compuesto heterocigoto en un gen ficticio (GENEX), un homocigoto
raro (GENEH), un par en cis (GENEC, debe bajar de ranking) y ruido.

Si das --header con la cabecera real *sin muestras* (`bcftools view -h -G`),
el VCF sintético reutiliza sus contigs e INFO/FORMAT, así los scripts ven el
mismo esquema que el archivo real. La cabecera no contiene genotipos.

Uso:
    mva-fixtures                         # cabecera mínima GRCh38
    mva-fixtures --header fixtures/header_nosamples.txt
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from mva import REPO_ROOT

SAMPLE = "SYNTH01"
ANNOT_COLUMNS = ["CHROM", "POS", "REF", "ALT", "FILTER", "GT", "SYMBOL", "Consequence", "IMPACT",
                 "gnomADe_AF", "gnomADg_AF", "MAX_AF", "CADD_PHRED", "REVEL",
                 "SpliceAI_pred_DS_AG", "SpliceAI_pred_DS_AL", "SpliceAI_pred_DS_DG", "SpliceAI_pred_DS_DL",
                 "CLIN_SIG", "Existing_variation"]

MIN_HEADER = """##fileformat=VCFv4.2
##reference=GRCh38_SYNTHETIC
##FILTER=<ID=PASS,Description="All filters passed">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype quality">
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">
##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths">
""" + "".join(f"##contig=<ID=chr{c}>\n" for c in [*range(1, 23), "X", "Y", "M"])

# Escenarios plantados: (gene, chrom, pos, ref, alt, gt, consequence, impact, af, cadd, revel, spliceai, clinsig, existing)
PLANTED = [
    # Par compuesto heterocigoto en trans (fase desconocida) -> debe quedar #1
    ("GENEX", "chr7", 1_000_100, "C", "T", "0/1", "stop_gained", "HIGH", 2e-6, 38.0, None, 0.0, "pathogenic", ""),
    ("GENEX", "chr7", 1_004_250, "G", "A", "0/1", "missense_variant", "MODERATE", 4e-5, 27.5, 0.81, 0.01, "", ""),
    # Homocigoto raro
    ("GENEH", "chr3", 5_000_000, "A", "G", "1/1", "missense_variant", "MODERATE", 1e-4, 24.0, 0.55, 0.0, "", ""),
    # Par en cis (fasado en el mismo haplotipo) -> no explica un modelo recesivo
    ("GENEC", "chr12", 2_000_000, "T", "C", "1|0", "frameshift_variant", "HIGH", 0.0, 35.0, None, 0.0, "", ""),
    ("GENEC", "chr12", 2_000_300, "G", "T", "1|0", "missense_variant", "MODERATE", 0.0, 29.0, 0.7, 0.0, "", ""),
    # Hipomorfo regulatorio "conocido" (rescatado por known_variants aunque sea MODIFIER)
    ("GENEK", "chr9", 3_000_000, "G", "A", "0/1", "upstream_gene_variant", "MODIFIER", 0.02, 8.0, None, 0.0, "", "rsSYNTH1"),
    ("GENEK", "chr9", 3_010_000, "C", "A", "0/1", "stop_gained", "HIGH", 1e-5, 36.0, None, 0.0, "", ""),
    # Variante común de alto impacto -> debe ser filtrada por AF
    ("GENEF", "chr2", 9_000_000, "A", "T", "0/1", "stop_gained", "HIGH", 0.08, 33.0, None, 0.0, "", ""),
    ("GENEF", "chr2", 9_000_500, "C", "G", "0/1", "missense_variant", "MODERATE", 0.05, 20.0, 0.2, 0.0, "", ""),
]

CONSEQ = [("synonymous_variant", "LOW"), ("intron_variant", "MODIFIER"), ("missense_variant", "MODERATE"),
          ("3_prime_UTR_variant", "MODIFIER"), ("splice_region_variant", "LOW"), ("intergenic_variant", "MODIFIER")]


def _fmt(x) -> str:
    return "" if x is None else str(x)


def make_rows(n_noise: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for g, c, p, r, a, gt, csq, imp, af, cadd, revel, sai, cs, ex in PLANTED:
        rows.append(dict(CHROM=c, POS=p, REF=r, ALT=a, FILTER="PASS", GT=gt, SYMBOL=g, Consequence=csq,
                         IMPACT=imp, gnomADe_AF=af, gnomADg_AF=af, MAX_AF=af, CADD_PHRED=cadd, REVEL=revel,
                         SpliceAI_pred_DS_AG=sai, SpliceAI_pred_DS_AL=0.0, SpliceAI_pred_DS_DG=0.0,
                         SpliceAI_pred_DS_DL=0.0, CLIN_SIG=cs, Existing_variation=ex))
    bases = "ACGT"
    for i in range(n_noise):
        csq, imp = rng.choice(CONSEQ)
        ref = rng.choice(bases)
        alt = rng.choice([b for b in bases if b != ref])
        af = rng.choice([0.3, 0.12, 0.04, 0.008, 0.0005])
        rows.append(dict(CHROM=f"chr{rng.randint(1, 22)}", POS=rng.randint(10_000, 200_000_000), REF=ref, ALT=alt,
                         FILTER=rng.choice(["PASS"] * 9 + ["LowQual"]), GT=rng.choice(["0/1", "0/1", "1/1"]),
                         SYMBOL=f"NOISE{i % 400}", Consequence=csq, IMPACT=imp, gnomADe_AF=af, gnomADg_AF=af,
                         MAX_AF=af, CADD_PHRED=round(rng.uniform(0, 22), 1),
                         REVEL=round(rng.uniform(0, 0.4), 3) if imp == "MODERATE" else None,
                         SpliceAI_pred_DS_AG=round(rng.uniform(0, 0.05), 2), SpliceAI_pred_DS_AL=0.0,
                         SpliceAI_pred_DS_DG=0.0, SpliceAI_pred_DS_DL=0.0, CLIN_SIG="", Existing_variation=""))
    rows.sort(key=lambda d: (d["CHROM"], d["POS"]))
    return rows


def write_annotated(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(ANNOT_COLUMNS) + "\n")
        for r in rows:
            fh.write("\t".join(_fmt(r[c]) for c in ANNOT_COLUMNS) + "\n")


def write_vcf(rows: list[dict], header: str, path: Path) -> None:
    lines = [ln for ln in header.strip().splitlines() if not ln.startswith("#CHROM")]
    if not any("ID=GT," in ln for ln in lines):
        lines.append('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">')
    lines.append("\t".join(["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT", SAMPLE]))
    for r in rows:
        lines.append("\t".join([r["CHROM"], str(r["POS"]), ".", r["REF"], r["ALT"], "50", r["FILTER"], ".",
                                "GT", r["GT"]]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--header", type=Path, help="cabecera real SIN muestras (bcftools view -h -G)")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "fixtures")
    ap.add_argument("--n-noise", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)

    header = args.header.read_text(encoding="utf-8") if args.header else MIN_HEADER
    if args.header and any(ln.startswith("#CHROM") and len(ln.split("\t")) > 8 for ln in header.splitlines()):
        raise SystemExit("La cabecera trae columnas de muestra. Regenérala con `bcftools view -h -G`.")
    args.out.mkdir(parents=True, exist_ok=True)
    rows = make_rows(args.n_noise, args.seed)
    write_vcf(rows, header, args.out / "synthetic.vcf")
    write_annotated(rows, args.out / "synthetic_annotated.tsv")
    print(f"Fixtures sintéticos: {len(rows)} variantes -> {args.out}/synthetic.vcf, synthetic_annotated.tsv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
