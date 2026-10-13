"""QC agregado: resume `bcftools stats` en un JSON chico para outputs/.

Solo conserva totales y razones (número de SNVs/indels, Ti/Tv, het/hom,
build de referencia), nunca posiciones. Es lo primero que el LLM puede ver.

Uso (lo corre el humano; lee zona roja):
    bcftools stats -s - data/x.vcf.gz > work/bcftools_stats.txt
    mva-qc work/bcftools_stats.txt --header work/header_nosamples.txt -o outputs/qc_summary.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_bcftools_stats(text: str) -> dict:
    sn: dict[str, int] = {}
    tstv = None
    het = hom_alt = None
    for line in text.splitlines():
        parts = line.split("\t")
        if parts[0] == "SN" and len(parts) >= 4:
            key = parts[2].rstrip(":").replace("number of ", "").strip()
            try:
                sn[key] = int(parts[3])
            except ValueError:
                pass
        elif parts[0] == "TSTV" and len(parts) >= 5 and tstv is None:
            tstv = float(parts[4])
        elif parts[0] == "PSC" and len(parts) >= 7:
            # PSC id sample nRefHom nNonRefHom nHets ...
            hom_alt, het = int(parts[4]), int(parts[5])
    out = {
        "n_samples": sn.get("samples"),
        "n_records": sn.get("records"),
        "n_snps": sn.get("SNPs"),
        "n_indels": sn.get("indels"),
        "n_multiallelic_sites": sn.get("multiallelic sites"),
        "ts_tv": tstv,
    }
    if het is not None and hom_alt:
        out["het_hom_ratio"] = round(het / hom_alt, 3)
    return out


def parse_header(text: str) -> dict:
    """Extrae build y convención de contigs de una cabecera SIN muestras."""
    contigs = re.findall(r"##contig=<ID=([^,>]+)", text)
    ref = re.search(r"##reference=(.+)", text)
    lengths = dict(re.findall(r"##contig=<ID=([^,>]+),length=(\d+)", text))
    chr1_len = lengths.get("chr1") or lengths.get("1")
    build = None
    if chr1_len:
        build = {"248956422": "GRCh38", "249250621": "GRCh37"}.get(chr1_len, "desconocido")
    return {
        "reference_line": ref.group(1).strip() if ref else None,
        "n_contigs": len(contigs),
        "chr_prefix": bool(contigs) and contigs[0].startswith("chr"),
        "build_from_chr1_length": build,
        "callers": sorted(set(re.findall(r"##(\w*[Cc]aller\w*|source|DRAGEN\w*|GATK\w*)", text)))[:10],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stats", type=Path)
    ap.add_argument("--header", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("outputs/qc_summary.json"))
    args = ap.parse_args(argv)
    summary = {"stats": parse_bcftools_stats(args.stats.read_text(encoding="utf-8"))}
    if args.header:
        summary["header"] = parse_header(args.header.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
