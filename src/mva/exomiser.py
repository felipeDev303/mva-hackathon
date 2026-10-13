"""Integración con Exomiser (>= 15.x).

1) `mva-exomiser-config`: toma el preset que trae la distribución de Exomiser
   (examples/preset-genome-analysis.yml) y le inyecta VCF, ensamblaje y HPO.
   Así no reescribimos el esquema YAML de Exomiser a mano.

2) `mva-exomiser-summary`: resume el TSV de genes de Exomiser (nivel gen, sin
   genotipos) en un top-N para outputs/.

Uso:
    mva-exomiser-config --preset $EXOMISER_HOME/examples/preset-genome-analysis.yml \
        --vcf work/normalized.vcf.gz -o work/exomiser-analysis.yml
    java -Xmx12g -jar $EXOMISER_HOME/exomiser-cli-15.1.0.jar analyse \
        --analysis work/exomiser-analysis.yml --output-directory work/exomiser \
        --output-format HTML,TSV_GENE,TSV_VARIANT
    mva-exomiser-summary work/exomiser/*genes.tsv -o outputs/exomiser_genes_top50.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from mva import REPO_ROOT, load_config, read_hpo_terms

GENE_COLS_KEEP = ["RANK", "GENE_SYMBOL", "ENTREZ_GENE_ID", "MOI", "P-VALUE",
                  "EXOMISER_GENE_COMBINED_SCORE", "EXOMISER_GENE_PHENO_SCORE",
                  "EXOMISER_GENE_VARIANT_SCORE", "HUMAN_PHENO_SCORE", "HUMAN_PHENO_EVIDENCE"]


def build_analysis(preset: dict, vcf: str, assembly: str, hpo: list[str]) -> dict:
    cfg = dict(preset)
    analysis = dict(cfg.get("analysis", {}))
    analysis["vcf"] = vcf
    analysis["genomeAssembly"] = {"GRCh38": "hg38", "GRCh37": "hg19"}.get(assembly, assembly)
    analysis["hpoIds"] = hpo
    # Sin pedigree: un solo probando, sin padres.
    analysis.setdefault("ped", None)
    cfg["analysis"] = analysis
    out = dict(cfg.get("outputOptions", {}) or {})
    out.setdefault("numGenes", 100)
    cfg["outputOptions"] = out
    return cfg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", type=Path, required=True, help="examples/preset-genome-analysis.yml de Exomiser")
    ap.add_argument("--vcf", required=True)
    ap.add_argument("-o", "--out", type=Path, default=Path("work/exomiser-analysis.yml"))
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    hpo = read_hpo_terms(REPO_ROOT / cfg["hpo_file"])
    if not hpo:
        raise SystemExit("config/hpo_terms.txt no tiene términos HPO; cópialos del dataset primero.")
    preset = yaml.safe_load(args.preset.read_text(encoding="utf-8"))
    analysis = build_analysis(preset, args.vcf, cfg["assembly"], hpo)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml.safe_dump(analysis, sort_keys=False), encoding="utf-8")
    print(f"Análisis Exomiser escrito en {args.out} ({len(hpo)} términos HPO)")
    return 0


def summarize_genes(df: pd.DataFrame, top: int) -> pd.DataFrame:
    df = df.rename(columns=lambda c: c.lstrip("#"))
    keep = [c for c in GENE_COLS_KEEP if c in df.columns]
    df = df[keep].copy()
    score = "EXOMISER_GENE_COMBINED_SCORE"
    if score in df.columns:
        df = df.sort_values(score, ascending=False)
    if "GENE_SYMBOL" in df.columns:
        df = df.drop_duplicates("GENE_SYMBOL")
    return df.head(top)


def summary_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resume el TSV de genes de Exomiser para outputs/")
    ap.add_argument("genes_tsv", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("outputs/exomiser_genes_top50.tsv"))
    ap.add_argument("--top", type=int, default=50)
    args = ap.parse_args(argv)
    df = pd.read_csv(args.genes_tsv, sep="\t")
    out = summarize_genes(df, args.top)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, sep="\t", index=False)
    print(f"{len(out)} genes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
