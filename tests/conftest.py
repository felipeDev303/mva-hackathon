import copy
from pathlib import Path

import pytest

from mva import REPO_ROOT, load_config
from mva.fixtures import make_rows, write_annotated, write_vcf, MIN_HEADER


@pytest.fixture(scope="session")
def cfg():
    c = load_config(REPO_ROOT / "config" / "config.yaml")
    c = copy.deepcopy(c)
    # Para los tests, el "hipomorfo conocido" es el sintético de GENEK.
    c["known_variants"] = [{"id": "rsSYNTH1", "gene": "GENEK", "note": "test"}]
    c["guard"]["sample_ids"] = ["SYNTH01"]
    return c


@pytest.fixture()
def synth(tmp_path: Path):
    rows = make_rows(n_noise=1500, seed=7)
    annotated = tmp_path / "annotated.tsv"
    vcf = tmp_path / "synthetic.vcf"
    write_annotated(rows, annotated)
    write_vcf(rows, MIN_HEADER, vcf)
    return {"annotated": annotated, "vcf": vcf, "dir": tmp_path}
