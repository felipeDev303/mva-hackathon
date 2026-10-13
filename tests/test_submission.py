import pandas as pd

from mva.prioritize import run as prioritize
from mva.submission import build, calibrate_epcr, norm_chrom, validate


def _submission(synth, cfg):
    out = synth["dir"] / "outputs"
    prioritize(synth["annotated"], cfg, out, synth["dir"] / "work" / "c.tsv")
    df = build(out / "top_pairs.tsv", cfg, temperature=0.1, overrides=None, secondary=None)
    path = synth["dir"] / "sub.csv"
    df.to_csv(path, index=False)
    return df, path


def test_build_produces_valid_csv(synth, cfg):
    df, path = _submission(synth, cfg)
    assert len(df) <= 10
    assert validate(path, cfg) == []
    assert df["epcr"].is_monotonic_decreasing
    assert df.loc[0, "chrom_1"].startswith("chr")


def test_single_variant_rows_leave_second_blank(synth, cfg):
    df, _ = _submission(synth, cfg)
    singles = df[df["notes"].str.contains("AR_hom|AD_single")]
    assert (singles["chrom_2"].fillna("") == "").all()


def test_validate_catches_errors(tmp_path, cfg):
    bad = tmp_path / "bad.csv"
    bad.write_text(
        "proband_id,chrom_1,pos_1,ref_1,alt_1,chrom_2,pos_2,ref_2,alt_2,epcr,finding_type\n"
        "PROBAND02,15,abc,G,A,,,,,1.5,primary\n")
    errs = " ".join(validate(bad, cfg))
    for needle in ("proband_id", "chrom_1", "pos_1", "epcr"):
        assert needle in errs


def test_validate_flags_too_many_rows(tmp_path, cfg):
    rows = [f"PROBAND01,chr1,{100 + i},A,G,,,,,{0.9 - i * 0.05:.2f},primary" for i in range(11)]
    p = tmp_path / "many.csv"
    p.write_text("proband_id,chrom_1,pos_1,ref_1,alt_1,chrom_2,pos_2,ref_2,alt_2,epcr,finding_type\n"
                 + "\n".join(rows) + "\n")
    assert any("máximo es 10" in e for e in validate(p, cfg))


def test_epcr_and_chrom_helpers():
    p = calibrate_epcr([0.9, 0.5, 0.1])
    assert p[0] > p[1] >= p[2] > 0 and all(0 < x <= 1 for x in p)
    assert norm_chrom("15") == "chr15" and norm_chrom("chrMT") == "chrM" and norm_chrom("") == ""
