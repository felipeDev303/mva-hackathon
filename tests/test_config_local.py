import mva


def test_local_config_overrides_paths_and_sample_ids(tmp_path, monkeypatch):
    local = tmp_path / "local.yaml"
    local.write_text("paths:\n  raw_vcf: data/x.vcf.gz\nguard:\n  sample_ids: [SYNTH01]\n", encoding="utf-8")
    monkeypatch.setattr(mva, "LOCAL_CONFIG", local)
    c = mva.load_config()
    assert c["paths"]["raw_vcf"] == "data/x.vcf.gz"
    assert c["paths"]["normalized_vcf"] == "work/normalized.vcf.gz"  # el resto de config.yaml se conserva
    assert c["guard"]["sample_ids"] == ["SYNTH01"] and c["guard"]["max_variant_rows"] == 50


def test_explicit_path_ignores_local_config(tmp_path, monkeypatch):
    local = tmp_path / "local.yaml"
    local.write_text("paths:\n  raw_vcf: data/x.vcf.gz\n", encoding="utf-8")
    monkeypatch.setattr(mva, "LOCAL_CONFIG", local)
    assert mva.load_config(mva.REPO_ROOT / "config" / "config.yaml")["paths"]["raw_vcf"] != "data/x.vcf.gz"
