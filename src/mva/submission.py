"""Construye y valida el CSV de entrega del Track 1.

Formato (tab "Submit - Track 1" + evaluation.py del Space):
    proband_id,chrom_1,pos_1,ref_1,alt_1,chrom_2,pos_2,ref_2,alt_2,epcr,finding_type,notes
  * proband_id = PROBAND01 · coordenadas GRCh38 · cromosoma con prefijo "chr"
  * máximo 10 filas, epcr en (0, 1], idealmente ordenadas por epcr descendente
  * *_2 vacío para propuestas de una sola variante
  * finding_type = primary | secondary (secondary no afecta el puntaje automático)

EPCR: por defecto se calibra con una softmax con temperatura sobre los scores
del top-10; puedes sobrescribirlo a mano con --epcr-overrides (rank,epcr).
Documenta en el write-up cuál usaste.

Uso:
    mva-submission build outputs/top_pairs.tsv -o submissions/track1_submission.csv
    mva-submission validate submissions/track1_submission.csv
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import re
import sys
from pathlib import Path

import pandas as pd

from mva import REPO_ROOT, load_config

COLUMNS = ["proband_id", "chrom_1", "pos_1", "ref_1", "alt_1", "chrom_2", "pos_2", "ref_2", "alt_2",
           "epcr", "finding_type", "notes"]
ALLELE = re.compile(r"^[ACGTN]+$")
CHROM = re.compile(r"^chr([1-9]|1[0-9]|2[0-2]|X|Y|M)$")


def norm_chrom(c: str, prefix: str = "chr") -> str:
    c = str(c).strip()
    if not c:
        return ""
    bare = c[3:] if c.lower().startswith("chr") else c
    bare = "M" if bare in ("MT", "M") else bare
    return f"{prefix}{bare}"


def calibrate_epcr(scores: list[float], temperature: float = 0.1, floor: float = 0.01) -> list[float]:
    """Softmax con temperatura → probabilidades que suman ~1, recortadas a (floor, 1]."""
    if not scores:
        return []
    m = max(scores)
    exps = [math.exp((s - m) / temperature) for s in scores]
    z = sum(exps)
    return [round(max(floor, min(1.0, e / z)), 4) for e in exps]


def build(top_pairs: Path, cfg: dict, temperature: float, overrides: Path | None,
          secondary: Path | None) -> pd.DataFrame:
    tp = pd.read_csv(top_pairs, sep="\t", dtype=str, keep_default_na=False).head(10)
    prefix = cfg.get("chrom_prefix", "chr")
    epcr = calibrate_epcr([float(x) for x in tp["score"]], temperature)
    rows = []
    for (_, r), e in zip(tp.iterrows(), epcr):
        rows.append({
            "proband_id": cfg["proband_id"],
            "chrom_1": norm_chrom(r["chrom_1"], prefix), "pos_1": r["pos_1"], "ref_1": r["ref_1"], "alt_1": r["alt_1"],
            "chrom_2": norm_chrom(r.get("chrom_2", ""), prefix), "pos_2": r.get("pos_2", ""),
            "ref_2": r.get("ref_2", ""), "alt_2": r.get("alt_2", ""),
            "epcr": e, "finding_type": "primary",
            "notes": f"{r['gene']} {r['model']} phase={r['phase']}",
        })
    df = pd.DataFrame(rows, columns=COLUMNS)
    if overrides and overrides.exists():
        ov = pd.read_csv(overrides)  # columnas: rank,epcr
        for _, o in ov.iterrows():
            df.loc[int(o["rank"]) - 1, "epcr"] = float(o["epcr"])
    if secondary and secondary.exists():
        sec = pd.read_csv(secondary, dtype=str, keep_default_na=False)
        sec["proband_id"] = cfg["proband_id"]
        sec["finding_type"] = "secondary"
        df = pd.concat([df, sec.reindex(columns=COLUMNS, fill_value="")], ignore_index=True)
    df = df.sort_values("epcr", ascending=False, kind="stable").head(10).reset_index(drop=True)
    return df


def validate(path: Path, cfg: dict) -> list[str]:
    errs: list[str] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)
    missing = [c for c in COLUMNS[:10] if c not in header]
    if missing:
        errs.append(f"faltan columnas: {missing}")
        return errs
    if not rows:
        errs.append("el CSV no tiene filas")
    if len(rows) > 10:
        errs.append(f"{len(rows)} filas; el máximo es 10")
    seen, last = set(), math.inf
    for i, r in enumerate(rows, start=2):
        if r["proband_id"].strip() != cfg["proband_id"]:
            errs.append(f"fila {i}: proband_id {r['proband_id']!r} != {cfg['proband_id']}")
        for s in ("1", "2"):
            c, p, ref, alt = (r.get(f"{k}_{s}", "").strip() for k in ("chrom", "pos", "ref", "alt"))
            if s == "2" and not any((c, p, ref, alt)):
                continue
            if not CHROM.match(c):
                errs.append(f"fila {i}: chrom_{s}={c!r} (se espera 'chr1'..'chr22','chrX','chrY','chrM')")
            if not p.isdigit():
                errs.append(f"fila {i}: pos_{s}={p!r} no es entero")
            for k, v in (("ref", ref), ("alt", alt)):
                if not ALLELE.match(v.upper()):
                    errs.append(f"fila {i}: {k}_{s}={v!r} no es un alelo ACGTN")
        try:
            e = float(r["epcr"])
            if not (0 < e <= 1):
                errs.append(f"fila {i}: epcr {e} fuera de (0, 1]")
            if e > last:
                errs.append(f"fila {i}: no está ordenado por epcr descendente (warning del evaluador)")
            last = e
        except ValueError:
            errs.append(f"fila {i}: epcr {r['epcr']!r} no es numérico")
        ft = (r.get("finding_type") or "primary").strip().lower()
        if ft not in ("primary", "secondary"):
            errs.append(f"fila {i}: finding_type {ft!r}")
        key = frozenset(filter(None, [(r["chrom_1"], r["pos_1"], r["ref_1"], r["alt_1"]),
                                      (r["chrom_2"], r["pos_2"], r["ref_2"], r["alt_2"]) if r["chrom_2"] else None]))
        if key in seen:
            errs.append(f"fila {i}: hipótesis duplicada")
        seen.add(key)
    return errs


def official_check(path: Path) -> str:
    """Si descargaste vendor/evaluation.py (make fetch-eval), corre su parser oficial."""
    ev = REPO_ROOT / "vendor" / "evaluation.py"
    if not ev.exists():
        return "vendor/evaluation.py no encontrado (corre `make fetch-eval` para validar con el parser oficial)"
    spec = importlib.util.spec_from_file_location("hf_evaluation", ev)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    parsed = mod.load_submission(str(path))
    return "parser oficial OK: " + ", ".join(f"{k}: {len(v)} filas" for k, v in parsed.items())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("top_pairs", type=Path)
    b.add_argument("-o", "--out", type=Path)
    b.add_argument("--temperature", type=float, default=0.1)
    b.add_argument("--epcr-overrides", type=Path)
    b.add_argument("--secondary", type=Path, help="CSV con hallazgos secundarios (mismas columnas)")
    v = sub.add_parser("validate")
    v.add_argument("csv", type=Path)
    ap.add_argument("--config", type=Path)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)

    if args.cmd == "build":
        out = args.out or REPO_ROOT / cfg["paths"]["submission_csv"]
        df = build(args.top_pairs, cfg, args.temperature, args.epcr_overrides, args.secondary)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        print(f"{len(df)} filas -> {out}")
        target = out
    else:
        target = args.csv

    errs = validate(target, cfg)
    if errs:
        print("VALIDACIÓN FALLÓ:")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("Validación local OK.")
    try:
        print(official_check(target))
    except Exception as exc:  # el parser oficial puede lanzar ValueError con un mensaje útil
        print(f"Parser oficial rechazó el archivo: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
