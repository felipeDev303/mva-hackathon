"""Integración con Exomiser (>= 15.x).

1) `mva-exomiser-config`: escribe la muestra como phenopacket v1 (id del probando
   y HPO de config/hpo_terms.txt). Exomiser 15 recibe muestra, VCF y análisis por
   separado (`--sample`, `--vcf`/`--assembly`, `--analysis`); el análisis es el
   preset de genoma que trae la distribución, sin reescribirlo.

2) `mva-exomiser-summary`: resume el TSV de genes de Exomiser (nivel gen, sin
   genotipos) en un top-N para outputs/.

Uso:
    mva-exomiser-config -o work/exomiser-sample.yml
    java -Xmx12g -jar $EXOMISER_HOME/exomiser-cli-15.1.0.jar analyse \
        --sample work/exomiser-sample.yml --vcf work/normalized.vcf.gz --assembly GRCh38 \
        --analysis $EXOMISER_HOME/examples/preset-genome-analysis.yml \
        --output-directory work/exomiser --output-filename exomiser \
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


def build_sample(proband_id: str, hpo: list[str]) -> dict:
    """Phenopacket v1 mínimo de un individuo, como el `--sample` de Exomiser 15.

    No lleva `htsFiles`: el VCF y el ensamblaje se pasan por línea de comandos.
    Sin pedigree: un solo probando, sin padres.
    """
    return {
        "id": proband_id,
        "subject": {"id": proband_id},
        "phenotypicFeatures": [{"type": {"id": term}} for term in hpo],
        "metaData": {
            "createdBy": "mva-exomiser-config",
            "resources": [{"id": "hp", "name": "human phenotype ontology", "namespacePrefix": "HP",
                           "url": "http://purl.obolibrary.org/obo/hp.owl",
                           "iriPrefix": "http://purl.obolibrary.org/obo/HP_"}],
            "phenopacketSchemaVersion": "1.0",
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", type=Path, default=Path("work/exomiser-sample.yml"))
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    hpo = read_hpo_terms(REPO_ROOT / cfg["hpo_file"])
    if not hpo:
        raise SystemExit("config/hpo_terms.txt no tiene términos HPO; cópialos del dataset primero.")
    sample = build_sample(cfg["proband_id"], hpo)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml.safe_dump(sample, sort_keys=False), encoding="utf-8")
    print(f"Muestra Exomiser escrita en {args.out} ({len(hpo)} términos HPO)")
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
