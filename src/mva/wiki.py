"""Mantenimiento de la wiki (docs/wiki/) desde la línea de comandos.

Genera notas con el frontmatter que espera el tablero de Dataview. Solo lee la
zona verde (outputs/, submissions/) y valida cada nota con mva-guard antes de
dejarla escrita: si una nota no pasa el guard, se borra y el comando falla.

Subcomandos:
    mva-wiki day                         diario de hoy (idempotente)
    mva-wiki run real-prioritize         nota de corrida con commit + resumen de outputs/
    mva-wiki adr "Peso de Exomiser 0.5"  nueva decisión con número correlativo
    mva-wiki sub                         nota del próximo envío (N = envíos previos + 1)

Los objetivos `make real-*` llaman a `mva-wiki run` al terminar.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from mva import REPO_ROOT, load_config
from mva.guard import Report, check_file

WIKI = REPO_ROOT / "docs" / "wiki"

PHASES = {
    "real-qc": "0-qc",
    "real-normalize": "1-anotacion",
    "real-annotate": "1-anotacion",
    "real-exomiser": "1-anotacion",
    "real-prioritize": "2-priorizacion",
    "real-phase": "3-fase",
    "real-submission": "5-entrega",
}


# ───────────────────────── utilidades ─────────────────────────

def today() -> str:
    return dt.date.today().isoformat()


def git_commit(root: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True).stdout.strip()
        return f"{out}-dirty" if dirty else out
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "sin-commit"


def slug(text: str) -> str:
    s = text.lower()
    for a, b in zip("áéíóúñü", "aeiounu"):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "sin-titulo"


def frontmatter(d: dict) -> str:
    lines = ["---"]
    for k, v in d.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(json.dumps(x, ensure_ascii=False) for x in v)}]")
        elif v is None:
            lines.append(f"{k}: ")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_sin filas_\n"
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r.values) + " |")
    return "\n".join(out) + "\n"


def write_guarded(path: Path, content: str, cfg: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    report = Report()
    check_file(path, cfg, report)
    if report.errors:
        path.unlink()
        raise SystemExit("Nota rechazada por el guard (no se escribió):\n  " + "\n  ".join(report.errors))
    return path


def unique_path(folder: Path, stem: str) -> Path:
    p = folder / f"{stem}.md"
    i = 2
    while p.exists():
        p = folder / f"{stem}-{i}.md"
        i += 1
    return p


# ───────────────────────── resúmenes de outputs/ ─────────────────────────

def summarize_outputs(target: str, outputs: Path, submissions: Path) -> tuple[str, list[str]]:
    """Devuelve (markdown, archivos usados). Solo lee zona verde y solo nivel gen/agregado."""
    parts, used = [], []

    def add(title: str, body: str, f: Path):
        parts.append(f"### {title}\n\n{body}")
        used.append(str(f.relative_to(f.parents[1])) if len(f.parents) > 1 else f.name)

    qc = outputs / "qc_summary.json"
    if target == "real-qc" and qc.exists():
        d = json.loads(qc.read_text(encoding="utf-8"))
        rows = [{"métrica": k, "valor": v} for k, v in {**d.get("stats", {}),
                **{f"header.{k}": v for k, v in d.get("header", {}).items() if k != "callers"}}.items()]
        add("QC", md_table(pd.DataFrame(rows)), qc)

    exo = outputs / "exomiser_genes_top50.tsv"
    if target == "real-exomiser" and exo.exists():
        t = pd.read_csv(exo, sep="\t")
        keep = [c for c in ("GENE_SYMBOL", "MOI", "EXOMISER_GENE_COMBINED_SCORE", "EXOMISER_GENE_PHENO_SCORE")
                if c in t.columns]
        add("Exomiser · top 10 genes", md_table(t[keep].head(10)), exo)

    funnel = outputs / "funnel.json"
    genes = outputs / "genes_ranked.tsv"
    if target == "real-prioritize":
        if funnel.exists():
            d = json.loads(funnel.read_text(encoding="utf-8"))
            add("Embudo", md_table(pd.DataFrame([{"paso": k, "n": v} for k, v in d.items()])), funnel)
        if genes.exists():
            t = pd.read_csv(genes, sep="\t")
            keep = [c for c in ("rank_with_prior", "rank_no_prior", "gene", "model", "phase", "score",
                                "score_no_prior", "panel") if c in t.columns]
            add("Top 10 genes", md_table(t[keep].head(10)), genes)

    phase = outputs / "phase_summary.tsv"
    if target == "real-phase" and phase.exists():
        t = pd.read_csv(phase, sep="\t")
        add("Fase por gen", md_table(t[[c for c in ("gene", "phase") if c in t.columns]]), phase)

    sub = submissions / "track1_submission.csv"
    if target == "real-submission" and sub.exists():
        add("Hipótesis del CSV", md_table(submission_hypotheses(sub)), sub)

    if not parts:
        parts.append("_Este paso no deja salidas verdes. Anota aquí conteos que hayas visto en la terminal._\n")
    return "\n".join(parts), used


def submission_hypotheses(csv: Path) -> pd.DataFrame:
    s = pd.read_csv(csv, dtype=str, keep_default_na=False)
    notes = s.get("notes", pd.Series([""] * len(s)))
    split = notes.str.extract(r"^(\S+)\s+(\S+)")
    return pd.DataFrame({"#": range(1, len(s) + 1), "gen": split[0].fillna(""), "modelo": split[1].fillna(""),
                         "EPCR": s["epcr"], "tipo": s.get("finding_type", "primary")})


# ───────────────────────── subcomandos ─────────────────────────

def cmd_day(wiki: Path, cfg: dict, fase: str | None) -> Path:
    path = wiki / "diario" / f"{today()}.md"
    if path.exists():
        return path
    body = (frontmatter({"tipo": "diario", "fecha": today(), "fase": fase})
            + f"# {today()}\n\n## Hecho\n- \n\n## Bloqueos\n- \n\n## Siguiente\n- [ ] \n\n"
            "## Enlaces del día\n- Corridas: \n- Decisiones: \n")
    return write_guarded(path, body, cfg)


def cmd_run(wiki: Path, cfg: dict, target: str, estado: str, outputs: Path, submissions: Path) -> Path:
    if target not in PHASES:
        raise SystemExit(f"objetivo desconocido {target!r}; usa uno de {', '.join(PHASES)}")
    fase = PHASES[target]
    summary, used = summarize_outputs(target, outputs, submissions)
    title = f"RUN-{today()}-{target.removeprefix('real-')}"
    path = unique_path(wiki / "corridas", title)
    body = (frontmatter({"tipo": "corrida", "fecha": today(), "fase": fase, "comando": f"make {target}",
                         "commit": git_commit(REPO_ROOT), "estado": estado, "outputs": used, "decisiones": []})
            + f"# {path.stem}\n\n## Qué cambió respecto de la corrida anterior\n- \n\n"
            f"## Resultado agregado\n\n{summary}\n## Interpretación\n- \n\n## Siguiente paso\n- [ ] \n")
    return write_guarded(path, body, cfg)


def cmd_adr(wiki: Path, cfg: dict, titulo: str, parametro: str | None) -> Path:
    folder = wiki / "decisiones"
    nums = [int(m.group(1)) for p in folder.glob("ADR-*.md") if (m := re.match(r"ADR-(\d+)", p.name))]
    n = max(nums, default=0) + 1
    adr_id = f"ADR-{n:03d}"
    path = folder / f"{adr_id}-{slug(titulo)}.md"
    body = (frontmatter({"tipo": "decision", "id": adr_id, "fecha": today(), "estado": "propuesta",
                         "parametro": parametro, "reemplaza": None})
            + f"# {adr_id} · {titulo}\n\n## Contexto\n\n## Opciones consideradas\n1. \n2. \n\n"
            "## Decisión\n\n## Evidencia\n- Corridas: \n- Literatura: \n\n## Consecuencias\n")
    return write_guarded(path, body, cfg)


def cmd_sub(wiki: Path, cfg: dict, submissions: Path) -> Path:
    folder = wiki / "envios"
    n = len(list(folder.glob("SUB-*.md"))) + 1
    if n > 6:
        print("Aviso: ya hay 6 notas de envío; el límite del Track 1 es 6.")
    csv = submissions / "track1_submission.csv"
    hyp = submission_hypotheses(csv) if csv.exists() else pd.DataFrame()
    first = f"{hyp.iloc[0]['gen']} {hyp.iloc[0]['modelo']}" if len(hyp) else None
    path = folder / f"SUB-{n}.md"
    body = (frontmatter({"tipo": "envio", "n": n, "fecha": today(), "commit": git_commit(REPO_ROOT),
                         "rank_points": None, "f_max": None, "hipotesis_1": first})
            + f"# SUB-{n}\n\n## Cambios respecto del envío anterior\n- \n\n## Criterio de EPCR\n\n"
            f"## Hipótesis enviadas\n\n{md_table(hyp) if len(hyp) else '_no se encontró el CSV_'}\n"
            "## Resultado\nRank points: · F-max: · Lectura del resultado:\n")
    return write_guarded(path, body, cfg)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wiki", type=Path, default=WIKI)
    ap.add_argument("--config", type=Path)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("day")
    d.add_argument("--fase")
    r = sub.add_parser("run")
    r.add_argument("target", help="objetivo de make, p. ej. real-prioritize")
    r.add_argument("--estado", default="ok", choices=["ok", "fallo", "parcial"])
    r.add_argument("--outputs", type=Path)
    r.add_argument("--submissions", type=Path)
    a = sub.add_parser("adr")
    a.add_argument("titulo")
    a.add_argument("--parametro")
    s = sub.add_parser("sub")
    s.add_argument("--submissions", type=Path)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    outputs = getattr(args, "outputs", None) or REPO_ROOT / cfg["paths"]["outputs_dir"]
    submissions = getattr(args, "submissions", None) or REPO_ROOT / "submissions"

    if args.cmd == "day":
        path = cmd_day(args.wiki, cfg, args.fase)
    elif args.cmd == "run":
        path = cmd_run(args.wiki, cfg, args.target, args.estado, outputs, submissions)
    elif args.cmd == "adr":
        path = cmd_adr(args.wiki, cfg, args.titulo, args.parametro)
    else:
        path = cmd_sub(args.wiki, cfg, submissions)
    print(f"Nota: {path.relative_to(args.wiki.parent.parent) if args.wiki == WIKI else path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
