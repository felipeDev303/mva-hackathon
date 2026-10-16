"""Guard de la frontera de datos.

Valida que todo lo que hay en outputs/ (zona verde) sea agregado y pequeño
antes de que un LLM lo lea o se suba a git. Sale con código 1 si encuentra:

  * columnas de genotipo (GT, AD, DP, GQ, PL...) o el id de la muestra,
  * más de `max_variant_rows` filas a nivel variante en un archivo,
  * líneas con forma de VCF (#CHROM o registros tabulados chr/pos/ref/alt),
  * archivos más grandes que `max_file_bytes`,
  * extensiones genómicas (.vcf, .bam, .cram, ...).

En notas de prosa (.md/.txt/.json, p. ej. la wiki) además rechaza genotipos
explícitos (0/1, 1|0, GT=...), el id de la muestra y más de `max_variant_rows`
coordenadas chrN:pos. Rechaza imágenes con "igv" en el nombre.

Uso:
    mva-guard                               # revisa outputs/
    mva-guard outputs submissions docs/wiki # lo que corre `make guard`
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from mva import REPO_ROOT, load_config

GENOMIC_SUFFIXES = (".vcf", ".vcf.gz", ".bcf", ".bam", ".cram", ".bai", ".crai",
                    ".fastq", ".fastq.gz", ".fq.gz", ".tbi", ".csi")
TEXT_SUFFIXES = (".tsv", ".csv", ".txt", ".json", ".md", ".jsonl")
CHROM_COLS = {"chrom", "chr", "chromosome", "chrom_1", "#chrom", "contig"}
POS_COLS = {"pos", "position", "pos_1", "start"}
VCF_RECORD = re.compile(r"^(chr)?([0-9]{1,2}|X|Y|MT?)\t\d+\t[^\t]*\t[ACGTN*,.<>]+\t[ACGTN*,.<>]+\t", re.I)
# Genotipo estilo VCF dentro de cualquier celda: 0/1, 1|0, 0/1:35:...
GT_TOKEN = re.compile(r"(?<![\w.])[0-9.][/|][0-9.](:|\b)")
# En prosa (markdown) solo los genotipos inequívocos, para no confundir fracciones como 3/4.
PROSE_GT = re.compile(r"(?<![\w./|])(0/1|1/0|0\|1|1\|0|1\|1|\./\.)(?![\w/|])|\bGT[=:]\s*[01.][/|][01.]")
# Coordenadas tipo chr15:40117088 o chr15 40117088 (cuenta cuántas hay en un texto).
COORD = re.compile(r"\bchr(?:[0-9]{1,2}|X|Y|M)[:\s,_-]+\d{4,}\b", re.I)
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".pdf")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    checked: int = 0

    def add(self, path: Path, msg: str) -> None:
        self.errors.append(f"{path}: {msg}")


def _sniff_delimiter(sample: str) -> str:
    return "\t" if sample.count("\t") >= sample.count(",") else ","


def check_file(path: Path, cfg: dict, report: Report) -> None:
    gcfg = cfg.get("guard", {})
    max_rows = int(gcfg.get("max_variant_rows", 50))
    max_bytes = int(gcfg.get("max_file_bytes", 1_000_000))
    forbidden = {c.upper() for c in gcfg.get("forbidden_columns", [])}
    sample_ids = {s.upper() for s in gcfg.get("sample_ids", [])}

    name = path.name.lower()
    if name.endswith(GENOMIC_SUFFIXES):
        report.add(path, "extensión genómica en zona verde")
        return
    if name.endswith(IMAGE_SUFFIXES) and "igv" in name:
        report.add(path, "captura de IGV en zona verde (muestra lecturas; déjala en work/igv/)")
        return
    if not name.endswith(TEXT_SUFFIXES):
        return  # imágenes, html propios, etc. no se inspeccionan
    report.checked += 1

    size = path.stat().st_size
    if size > max_bytes:
        report.add(path, f"archivo de {size} bytes > límite {max_bytes}")
        return

    text = path.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), start=1):
        if line.startswith("#CHROM") or line.startswith("##fileformat=VCF"):
            report.add(path, f"línea {i}: cabecera VCF")
            return
        if VCF_RECORD.match(line):
            report.add(path, f"línea {i}: registro con forma de VCF")
            return

    upper_text = text.upper()
    for sid in sample_ids:
        if sid and re.search(rf"(?<![A-Z0-9]){re.escape(sid)}(?![A-Z0-9])", upper_text):
            report.add(path, "contiene el id de la muestra")
            return

    if not name.endswith((".tsv", ".csv")):
        # Notas en prosa (wiki, write-up): genotipos explícitos y listas largas de coordenadas.
        for i, line in enumerate(text.splitlines(), start=1):
            if PROSE_GT.search(line):
                report.add(path, f"línea {i}: genotipo explícito ({PROSE_GT.search(line).group(0)!r})")
                return
        n_coords = len(COORD.findall(text))
        if n_coords > max_rows:
            report.add(path, f"{n_coords} coordenadas genómicas > límite {max_rows}")
        return

    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    if not lines:
        return
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=_sniff_delimiter(lines[0]))
    rows = list(reader)
    header = [h.strip() for h in rows[0]]
    upper = {h.upper() for h in header}

    bad_cols = sorted((upper & forbidden) | (upper & sample_ids))
    if bad_cols:
        report.add(path, f"columnas prohibidas: {', '.join(bad_cols)}")

    lower = {h.lower() for h in header}
    variant_level = bool(lower & CHROM_COLS) and bool(lower & POS_COLS)
    n_rows = len(rows) - 1
    if variant_level and n_rows > max_rows:
        report.add(path, f"{n_rows} filas a nivel variante > límite {max_rows}")

    for r_i, row in enumerate(rows[1:], start=2):
        for cell in row:
            if GT_TOKEN.search(cell.strip()) and len(cell.strip()) <= 40:
                report.add(path, f"fila {r_i}: celda con forma de genotipo ({cell.strip()!r})")
                return


def run(paths: list[Path], cfg: dict) -> Report:
    report = Report()
    for root in paths:
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
        for f in files:
            if f.name == ".gitkeep" or ".obsidian" in f.parts or ".trash" in f.parts:
                continue
            check_file(f, cfg, report)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    paths = args.paths or [REPO_ROOT / cfg["paths"]["outputs_dir"]]
    report = run(paths, cfg)
    if report.errors:
        print(f"GUARD FALLÓ ({len(report.errors)} problema(s)). No compartas estos archivos con el LLM:")
        for e in report.errors:
            print(f"  ✗ {e}")
        return 1
    print(f"GUARD OK: {report.checked} archivo(s) de texto revisados, sin datos a nivel genoma.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
