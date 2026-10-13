from mva.guard import run
from mva.prioritize import run as prioritize


def test_guard_passes_on_pipeline_outputs(synth, cfg):
    out = synth["dir"] / "outputs"
    prioritize(synth["annotated"], cfg, out, synth["dir"] / "work" / "c.tsv")
    report = run([out], cfg)
    assert report.errors == [], report.errors
    assert report.checked >= 3


def test_guard_blocks_red_zone_table(synth, cfg):
    # La tabla de candidatos de work/ (con GT) nunca debe pasar.
    work = synth["dir"] / "work"
    prioritize(synth["annotated"], cfg, synth["dir"] / "o", work / "c.tsv")
    report = run([work], cfg)
    assert any("prohibidas" in e or "genotipo" in e or "filas" in e for e in report.errors)


def test_guard_blocks_vcf_and_long_tables(tmp_path, synth, cfg):
    (tmp_path / "leak.vcf").write_text("##fileformat=VCFv4.2\n")
    rows = "\n".join(f"chr1\t{i}\tA\tG" for i in range(100))
    (tmp_path / "big.tsv").write_text("chrom\tpos\tref\talt\n" + rows + "\n")
    (tmp_path / "pasted.txt").write_text(synth["vcf"].read_text().splitlines()[-1] + "\n")
    report = run([tmp_path], cfg)
    msgs = " ".join(report.errors)
    assert "extensión genómica" in msgs
    assert "filas a nivel variante" in msgs or "forma de VCF" in msgs
    assert "pasted.txt" in msgs


def test_guard_blocks_sample_id_column(tmp_path, cfg):
    (tmp_path / "x.tsv").write_text("gene\tSYNTH01\nBUB1B\t1\n")
    assert run([tmp_path], cfg).errors
