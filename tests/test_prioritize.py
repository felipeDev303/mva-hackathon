import json

import pandas as pd

from mva.prioritize import (build_hypotheses, filter_candidates, load_annotated, load_phase, phase_factor,
                            run, variant_score)


def _run(synth, cfg, **kw):
    out = synth["dir"] / "outputs"
    funnel = run(synth["annotated"], cfg, out, synth["dir"] / "work" / "cand.tsv", **kw)
    return funnel, out


def test_planted_scenarios_beat_noise(synth, cfg):
    _, out = _run(synth, cfg)
    top = pd.read_csv(out / "top_pairs.tsv", sep="\t")
    planted = top[~top["gene"].str.startswith("NOISE")]
    # Los tres escenarios recesivos plantados ocupan el top-3, por delante de todo el ruido
    assert set(top.head(3)["gene"]) == {"GENEX", "GENEK", "GENEH"}
    assert planted.index.max() < top[top["gene"].str.startswith("NOISE")].index.min()
    genex = top[(top["gene"] == "GENEX") & (top["model"] == "AR_comphet")].iloc[0]
    assert {genex["pos_1"], genex["pos_2"]} == {1_000_100, 1_004_250}


def _hypotheses(synth, cfg, phase=None):
    df = load_annotated(synth["annotated"], cfg)
    cand, _ = filter_candidates(df, cfg)
    cand["vscore"] = variant_score(cand, cfg)
    return build_hypotheses(cand, cfg, None, phase)


def test_cis_pair_is_penalized(synth, cfg):
    hyp = _hypotheses(synth, cfg)
    comphet = hyp[hyp["model"] == "AR_comphet"]
    genec = comphet[comphet["gene"] == "GENEC"]
    genex = comphet[comphet["gene"] == "GENEX"]
    assert genec["phase"].iloc[0] == "cis"
    assert genec.index.min() > genex.index.min()


def test_common_variants_filtered(synth, cfg):
    _, out = _run(synth, cfg)
    genes = pd.read_csv(out / "genes_ranked.tsv", sep="\t")
    assert "GENEF" not in set(genes["gene"])


def test_known_hypomorph_rescued(synth, cfg):
    _, out = _run(synth, cfg)
    top = pd.read_csv(out / "top_pairs.tsv", sep="\t")
    assert ((top["gene"] == "GENEK") & (top["model"] == "AR_comphet")).any()


def test_phase_override_from_summary(synth, cfg):
    phase = synth["dir"] / "phase_summary.tsv"
    pd.DataFrame([dict(gene="GENEX", chrom_1="chr7", pos_1=1_000_100, chrom_2="chr7", pos_2=1_004_250,
                       phase="cis")]).to_csv(phase, sep="\t", index=False)
    _, out = _run(synth, cfg, phase_tsv=phase)
    top = pd.read_csv(out / "top_pairs.tsv", sep="\t")
    assert not ((top.loc[0, "gene"] == "GENEX") and (top.loc[0, "model"] == "AR_comphet"))
    hyp = _hypotheses(synth, cfg, load_phase(phase))
    row = hyp[(hyp["gene"] == "GENEX") & (hyp["model"] == "AR_comphet")].iloc[0]
    assert row["phase"] == "cis"


def test_funnel_is_monotonic_and_aggregate(synth, cfg):
    funnel, out = _run(synth, cfg)
    saved = json.loads((out / "funnel.json").read_text())
    steps = [v for k, v in saved.items() if k not in ("genes_with_hypothesis", "hypotheses")]
    assert steps == sorted(steps, reverse=True)
    assert saved == funnel


def test_outputs_have_no_genotypes(synth, cfg):
    _, out = _run(synth, cfg)
    for f in ("top_pairs.tsv", "genes_ranked.tsv"):
        cols = set(pd.read_csv(out / f, sep="\t").columns)
        assert not cols & {"gt", "GT", "AD", "DP", "GQ"}


def test_phase_factor():
    assert phase_factor("0|1", "1|0")[1] == "trans"
    assert phase_factor("1|0", "1|0")[1] == "cis"
    assert phase_factor("0/1", "0/1")[1] == "unknown"
