"""Priorización de variantes y pares compuestos heterocigotos.

Entrada (zona roja):  work/annotated.tsv  (bcftools +split-vep, una fila por variante)
Salidas:
  work/candidate_variants.tsv   (ROJA)  todas las variantes que pasan filtros, con GT
  outputs/funnel.json           (VERDE) cuántas variantes sobreviven a cada filtro
  outputs/genes_ranked.tsv      (VERDE) top-50 genes, sin coordenadas ni genotipos
  outputs/top_pairs.tsv         (VERDE) top-10 hipótesis (pares o variantes), sin GT

Modelo:
  score_variante = Σ w_i · componente_i   (impacto, CADD, REVEL, SpliceAI, ClinVar), en [0, 1]
  score_par      = min(score_v1, score_v2) · fase · (1 - w_pheno + w_pheno · pheno_gen)
  score_gen_final = score_par · prior_gen    (también se reporta sin prior)

Es deliberadamente simple y transparente: cada número del write-up se puede
recalcular a mano desde config.yaml.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import pandas as pd

from mva import REPO_ROOT, load_config

HET = {"0/1", "1/0", "0|1", "1|0"}
HOM = {"1/1", "1|1"}


# ───────────────────────── utilidades ─────────────────────────

def _num(series: pd.Series) -> pd.Series:
    """Convierte a float; VEP usa '', '.', y listas 'a&b' -> toma el máximo."""
    def conv(x):
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return math.nan
        s = str(x).strip()
        if s in ("", ".", "-"):
            return math.nan
        vals = []
        for part in s.replace(",", "&").split("&"):
            try:
                vals.append(float(part))
            except ValueError:
                pass
        return max(vals) if vals else math.nan
    return series.map(conv)


def _cols(df: pd.DataFrame, spec) -> list[str]:
    spec = spec if isinstance(spec, list) else [spec]
    return [c for c in spec if c in df.columns]


def load_annotated(path: Path, cfg: dict) -> pd.DataFrame:
    c = cfg["columns"]
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    df = df.rename(columns=lambda x: x.lstrip("#").strip())
    out = pd.DataFrame({
        "chrom": df[c["chrom"]], "pos": df[c["pos"]].astype(int), "ref": df[c["ref"]], "alt": df[c["alt"]],
        "gt": df[c["gt"]].str.split(":").str[0], "gene": df[c["gene"]].replace("", pd.NA),
        "consequence": df.get(c["consequence"], ""), "impact": df.get(c["impact"], "MODIFIER"),
        "filter": df.get("FILTER", "PASS"),
        "existing": df.get(c.get("existing", "Existing_variation"), ""),
        "clinvar": df.get(c["clinvar"], "").fillna("").str.lower() if c["clinvar"] in df.columns else "",
    })
    af_cols = _cols(df, c["af"])
    out["af"] = pd.concat([_num(df[a]) for a in af_cols], axis=1).max(axis=1) if af_cols else math.nan
    out["cadd"] = _num(df[c["cadd"]]) if c["cadd"] in df.columns else math.nan
    out["revel"] = _num(df[c["revel"]]) if c["revel"] in df.columns else math.nan
    sai = _cols(df, c["spliceai"])
    out["spliceai"] = pd.concat([_num(df[s]) for s in sai], axis=1).max(axis=1) if sai else math.nan
    return out


def known_mask(df: pd.DataFrame, cfg: dict) -> pd.Series:
    ids = {k["id"] for k in cfg.get("known_variants", []) if k.get("id")}
    if not ids:
        return pd.Series(False, index=df.index)
    return df["existing"].fillna("").map(lambda s: bool(ids & set(str(s).replace(",", "&").split("&"))))


# ───────────────────────── scoring ─────────────────────────

def variant_score(df: pd.DataFrame, cfg: dict) -> pd.Series:
    s = cfg["scoring"]
    w = s["weights"]
    impact = df["impact"].map(s["impact_base"]).fillna(0.1)
    cadd = (df["cadd"] / 40).clip(0, 1).fillna(0)
    revel = df["revel"].clip(0, 1).fillna(0)
    sai = df["spliceai"].clip(0, 1).fillna(0)
    clin = df["clinvar"].map(
        lambda x: 1.0 if ("pathogenic" in x and "likely" not in x and "conflicting" not in x)
        else (0.5 if "likely_pathogenic" in x else 0.0))
    total = (w["impact"] * impact + w["cadd"] * cadd + w["revel"] * revel
             + w["spliceai"] * sai + w["clinvar"] * clin)
    return (total / sum(w.values())).round(4)


def gene_prior(gene: str, cfg: dict) -> tuple[float, str]:
    gp = cfg.get("gene_prior", {})
    best, label = gp.get("default", 0.5), "none"
    for name, panel in (gp.get("panels") or {}).items():
        if gene in panel.get("genes", []) and panel["weight"] > best:
            best, label = panel["weight"], name
    return best, label


def phase_factor(gt1: str, gt2: str) -> tuple[float, str]:
    """Si ambos GT están fasados (|) podemos saber cis/trans; si no, 'unknown'."""
    if "|" in gt1 and "|" in gt2:
        h1 = gt1.split("|").index("1") if "1" in gt1.split("|") else None
        h2 = gt2.split("|").index("1") if "1" in gt2.split("|") else None
        if h1 is not None and h2 is not None:
            return (0.2, "cis") if h1 == h2 else (1.0, "trans")
    return (0.8, "unknown")


# ───────────────────────── pipeline ─────────────────────────

def filter_candidates(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    f = cfg["filters"]
    funnel = {"input": int(len(df))}
    known = known_mask(df, cfg)

    if f.get("require_pass", True):
        df, known = df[df["filter"].isin(["PASS", "."])], known[df["filter"].isin(["PASS", "."])]
    funnel["pass_filter"] = int(len(df))

    nonref = df["gt"].isin(HET | HOM)
    df, known = df[nonref], known[nonref]
    funnel["non_reference_gt"] = int(len(df))

    has_gene = df["gene"].notna()
    df, known = df[has_gene], known[has_gene]
    funnel["in_gene"] = int(len(df))

    rare = df["af"].fillna(0) <= f["af_max_recessive"]
    df, known = df[rare | known], known[rare | known]
    funnel["rare_af_le_%s" % f["af_max_recessive"]] = int(len(df))

    functional = df["impact"].isin(f["keep_impacts"]) | (df["spliceai"].fillna(0) >= f["spliceai_min"]) \
        | df["clinvar"].str.contains("pathogenic", na=False)
    df = df[functional | known].copy()
    df["known_rescue"] = known[functional | known] & ~functional
    funnel["functional_or_known"] = int(len(df))
    return df, funnel


PHASE_FACTOR = {"trans": 1.0, "unknown": 0.8, "cis": 0.2}


def load_phase(path: Path | None) -> dict[tuple, str]:
    """outputs/phase_summary.tsv (de scripts/50_phase_and_review.sh) -> {(c1,p1,c2,p2): fase}."""
    if not path or not path.exists():
        return {}
    t = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    out = {}
    for _, r in t.iterrows():
        a, b = (r["chrom_1"], int(r["pos_1"])), (r["chrom_2"], int(r["pos_2"]))
        out[tuple(sorted([a, b]))] = r["phase"]
    return out


def build_hypotheses(cand: pd.DataFrame, cfg: dict, pheno: dict[str, float] | None = None,
                     phase_overrides: dict[tuple, str] | None = None) -> pd.DataFrame:
    s = cfg["scoring"]
    k = int(s.get("max_pairs_per_gene", 3))
    w_ph = float(s.get("exomiser_pheno_weight", 0.0)) if pheno else 0.0
    af_dom = cfg["filters"]["af_max_dominant"]
    mw = {"AR_comphet": 1.0, "AR_hom": 1.0, "AD_single": 0.3, **(s.get("model_weights") or {})}
    rows = []
    for gene, g in cand.groupby("gene"):
        g = g.sort_values("vscore", ascending=False)
        ph = (pheno or {}).get(gene, 0.0)
        ph_factor = (1 - w_ph) + w_ph * ph
        prior, panel = gene_prior(gene, cfg)
        top = g.head(k)
        # Recesivo: homocigoto
        for _, v in top[top["gt"].isin(HOM)].iterrows():
            rows.append(dict(gene=gene, model="AR_hom", v1=v, v2=None, phase="hom",
                             raw=v["vscore"] * mw["AR_hom"] * ph_factor, prior=prior, panel=panel, pheno=ph))
        # Recesivo: compuesto heterocigoto
        hets = top[top["gt"].isin(HET)]
        for (_, a), (_, b) in itertools.combinations(hets.iterrows(), 2):
            pf, ph_lab = phase_factor(a["gt"], b["gt"])
            key = tuple(sorted([(a["chrom"], int(a["pos"])), (b["chrom"], int(b["pos"]))]))
            if phase_overrides and key in phase_overrides:
                ph_lab = phase_overrides[key]
                pf = PHASE_FACTOR.get(ph_lab, 0.8)
            rows.append(dict(gene=gene, model="AR_comphet", v1=a, v2=b, phase=ph_lab,
                             raw=min(a["vscore"], b["vscore"]) * pf * mw["AR_comphet"] * ph_factor,
                             prior=prior, panel=panel, pheno=ph))
        # Dominante / de novo: una sola variante ultra rara (penalizada vs. recesivo)
        for _, v in hets[hets["af"].fillna(0) <= af_dom].iterrows():
            rows.append(dict(gene=gene, model="AD_single", v1=v, v2=None, phase="na",
                             raw=v["vscore"] * mw["AD_single"] * ph_factor, prior=prior, panel=panel, pheno=ph))
    if not rows:
        return pd.DataFrame()
    hyp = pd.DataFrame(rows)
    hyp["score_no_prior"] = hyp["raw"].round(4)
    hyp["score"] = (hyp["raw"] * hyp["prior"]).round(4)
    return hyp.sort_values(["score", "score_no_prior"], ascending=False).reset_index(drop=True)


def _variant_cols(v, suffix: str) -> dict:
    if v is None:
        return {f"chrom_{suffix}": "", f"pos_{suffix}": "", f"ref_{suffix}": "", f"alt_{suffix}": "",
                f"csq_{suffix}": "", f"vscore_{suffix}": ""}
    return {f"chrom_{suffix}": v["chrom"], f"pos_{suffix}": int(v["pos"]), f"ref_{suffix}": v["ref"],
            f"alt_{suffix}": v["alt"], f"csq_{suffix}": v["consequence"], f"vscore_{suffix}": v["vscore"]}


def top_pairs_table(hyp: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    out = []
    for i, h in hyp.head(n).iterrows():
        out.append({"rank": i + 1, "gene": h["gene"], "model": h["model"], "phase": h["phase"],
                    **_variant_cols(h["v1"], "1"), **_variant_cols(h["v2"], "2"),
                    "score": h["score"], "score_no_prior": h["score_no_prior"], "panel": h["panel"]})
    return pd.DataFrame(out)


def genes_table(hyp: pd.DataFrame, cand: pd.DataFrame, n: int = 50) -> pd.DataFrame:
    best = hyp.drop_duplicates("gene")
    counts = cand.groupby("gene").size().rename("n_candidate_variants")
    rank_np = hyp.sort_values("score_no_prior", ascending=False).drop_duplicates("gene")
    rank_np = rank_np.reset_index(drop=True).reset_index().set_index("gene")["index"] + 1
    t = best[["gene", "model", "phase", "score", "score_no_prior", "panel", "pheno"]].copy()
    t = t.join(counts, on="gene")
    t["rank_with_prior"] = range(1, len(t) + 1)
    t["rank_no_prior"] = t["gene"].map(rank_np)
    return t.head(n).reset_index(drop=True)


def load_pheno(path: Path | None) -> dict[str, float] | None:
    if not path or not path.exists():
        return None
    df = pd.read_csv(path, sep="\t").rename(columns=lambda c: c.lstrip("#"))
    if {"GENE_SYMBOL", "EXOMISER_GENE_PHENO_SCORE"} <= set(df.columns):
        return df.groupby("GENE_SYMBOL")["EXOMISER_GENE_PHENO_SCORE"].max().to_dict()
    return None


def run(annotated: Path, cfg: dict, outputs: Path, candidates_out: Path, pheno_tsv: Path | None = None,
        phase_tsv: Path | None = None) -> dict:
    df = load_annotated(annotated, cfg)
    cand, funnel = filter_candidates(df, cfg)
    cand["vscore"] = variant_score(cand, cfg)
    floor = float(cfg["scoring"].get("known_variant_floor", 0.0))
    cand.loc[known_mask(cand, cfg), "vscore"] = cand.loc[known_mask(cand, cfg), "vscore"].clip(lower=floor)
    hyp = build_hypotheses(cand, cfg, load_pheno(pheno_tsv), load_phase(phase_tsv))
    funnel["genes_with_hypothesis"] = int(hyp["gene"].nunique()) if len(hyp) else 0
    funnel["hypotheses"] = int(len(hyp))

    candidates_out.parent.mkdir(parents=True, exist_ok=True)
    cand.sort_values("vscore", ascending=False).to_csv(candidates_out, sep="\t", index=False)  # ROJA

    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "funnel.json").write_text(json.dumps(funnel, indent=2), encoding="utf-8")
    if len(hyp):
        genes_table(hyp, cand).to_csv(outputs / "genes_ranked.tsv", sep="\t", index=False)
        top_pairs_table(hyp).to_csv(outputs / "top_pairs.tsv", sep="\t", index=False)
    return funnel


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annotated", type=Path)
    ap.add_argument("--outputs", type=Path)
    ap.add_argument("--candidates", type=Path)
    ap.add_argument("--exomiser-genes", type=Path, help="TSV de genes de Exomiser (opcional)")
    ap.add_argument("--phase", type=Path, help="outputs/phase_summary.tsv (opcional)")
    ap.add_argument("--config", type=Path)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    p = cfg["paths"]
    funnel = run(args.annotated or REPO_ROOT / p["annotated_tsv"], cfg,
                 args.outputs or REPO_ROOT / p["outputs_dir"],
                 args.candidates or REPO_ROOT / p["candidates_tsv"], args.exomiser_genes, args.phase)
    # Solo agregados a stdout: nunca filas de variantes.
    print(json.dumps(funnel, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
