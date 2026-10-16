import json

import pandas as pd
import pytest

from mva import REPO_ROOT
from mva.guard import run as guard
from mva.prioritize import run as prioritize
from mva.submission import build
from mva.wiki import cmd_adr, cmd_day, cmd_run, cmd_sub, today

WIKI_FOLDERS = ("diario", "corridas", "decisiones", "envios")


@pytest.fixture()
def green(synth, cfg, tmp_path):
    """outputs/ y submissions/ sintéticos + una wiki vacía."""
    out, subs, wiki = tmp_path / "outputs", tmp_path / "submissions", tmp_path / "wiki"
    prioritize(synth["annotated"], cfg, out, tmp_path / "work" / "c.tsv")
    subs.mkdir()
    build(out / "top_pairs.tsv", cfg, 0.1, None, None).to_csv(subs / "track1_submission.csv", index=False)
    for f in WIKI_FOLDERS:
        (wiki / f).mkdir(parents=True)
    return {"outputs": out, "subs": subs, "wiki": wiki}


def _front(path):
    text = path.read_text(encoding="utf-8")
    head = text.split("---")[1]
    return dict(line.split(": ", 1) for line in head.strip().splitlines() if ": " in line), text


def test_run_note_has_frontmatter_and_aggregates(green, cfg):
    p = cmd_run(green["wiki"], cfg, "real-prioritize", "ok", green["outputs"], green["subs"])
    fm, text = _front(p)
    assert fm["tipo"] == "corrida" and fm["fase"] == "2-priorizacion" and fm["comando"] == "make real-prioritize"
    assert "funnel.json" in fm["outputs"] and fm["commit"]
    assert "### Embudo" in text and "GENEX" in text
    assert "0/1" not in text and "chr7" not in text  # nivel gen: ni genotipos ni coordenadas
    assert guard([p], cfg).errors == []


def test_run_notes_do_not_overwrite(green, cfg):
    a = cmd_run(green["wiki"], cfg, "real-prioritize", "ok", green["outputs"], green["subs"])
    b = cmd_run(green["wiki"], cfg, "real-prioritize", "ok", green["outputs"], green["subs"])
    assert a != b and a.exists() and b.exists()


def test_unknown_target_rejected(green, cfg):
    with pytest.raises(SystemExit):
        cmd_run(green["wiki"], cfg, "real-hack", "ok", green["outputs"], green["subs"])


def test_day_is_idempotent(green, cfg):
    p = cmd_day(green["wiki"], cfg, "2-priorizacion")
    p.write_text(p.read_text() + "\nnota mía\n")
    assert cmd_day(green["wiki"], cfg, None) == p and "nota mía" in p.read_text()
    assert p.name == f"{today()}.md"


def test_adr_numbering(green, cfg):
    (green["wiki"] / "decisiones" / "ADR-006-wiki.md").write_text("---\ntipo: decision\n---\n")
    p = cmd_adr(green["wiki"], cfg, "Peso de Exomiser 0.5", "scoring.exomiser_pheno_weight")
    assert p.name == "ADR-007-peso-de-exomiser-0-5.md"
    assert _front(p)[0]["estado"] == "propuesta"


def test_submission_note(green, cfg):
    p = cmd_sub(green["wiki"], cfg, green["subs"])
    fm, text = _front(p)
    assert p.name == "SUB-1.md" and fm["n"] == "1" and fm["hipotesis_1"]
    assert "| # | gen | modelo | EPCR | tipo |" in text
    assert cmd_sub(green["wiki"], cfg, green["subs"]).name == "SUB-2.md"


def test_guard_blocks_leaky_notes(tmp_path, cfg):
    (tmp_path / "gt.md").write_text("La variante en chr7 es 0/1 según el VCF.\n")
    (tmp_path / "gt2.md").write_text("GT=1|0 en la lectura\n")
    (tmp_path / "id.md").write_text("Muestra synth01 revisada\n")
    coords = "\n".join(f"- chr1:{1_000_000 + i}" for i in range(60))
    (tmp_path / "coords.md").write_text(coords + "\n")
    (tmp_path / "BUB1B_igv.png").write_bytes(b"\x89PNG")
    errs = " ".join(guard([tmp_path], cfg).errors)
    for name in ("gt.md", "gt2.md", "id.md", "coords.md", "BUB1B_igv.png"):
        assert name in errs, name


def test_guard_allows_normal_prose(tmp_path, cfg):
    (tmp_path / "ok.md").write_text(
        "# Nota\n\nEl par en chr15:40117088 (rs576524605) queda 3/4 del score. Tabla:\n\n"
        "| gen | n |\n| --- | --- |\n| BUB1B | 2 |\n")
    assert guard([tmp_path], cfg).errors == []


def test_seed_wiki_passes_guard(cfg):
    report = guard([REPO_ROOT / "docs" / "wiki"], cfg)
    assert report.errors == [], report.errors
    assert report.checked >= 20


def test_hook_parses_make_targets():
    import importlib.util
    spec = importlib.util.spec_from_file_location("hook", REPO_ROOT / ".claude" / "hooks" / "data_boundary.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.runs_real_target("cd x && make real-qc")
    assert m.runs_real_target("make NOWIKI=1 real-prioritize PHASE=outputs/phase_summary.tsv")
    assert not m.runs_real_target('make wiki-adr T="peso exomiser 0.5"')
    assert not m.runs_real_target("mva-wiki run real-prioritize")
    assert m.blocked_reason("Bash", {"command": "mva-wiki run real-prioritize"}) is None
