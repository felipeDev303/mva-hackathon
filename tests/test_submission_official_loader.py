from mva.submission import load_module

EVAL_LIKE = """from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Row:
    epcr: float
    rank: int | None = None


def load_submission(path):
    return {"PROBAND01": [Row(epcr=0.9, rank=1)]}
"""


def test_load_module_supports_future_annotations_dataclasses(tmp_path):
    ev = tmp_path / "evaluation.py"
    ev.write_text(EVAL_LIKE, encoding="utf-8")
    mod = load_module(ev, "fake_hf_evaluation")
    assert mod.load_submission("x.csv")["PROBAND01"][0].rank == 1
