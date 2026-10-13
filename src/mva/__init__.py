"""MVA Hackathon 2026 – pipeline de priorización de variantes (Track 1).

Convención de zonas:
    data/, work/   -> ZONA ROJA: datos del paciente. Solo los lee el humano / los scripts locales.
    outputs/       -> ZONA VERDE: agregados validados por `mva-guard`. Puede verlos el LLM.
    fixtures/      -> datos sintéticos para tests.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict:
    """Carga config/config.yaml (o la ruta dada)."""
    cfg_path = Path(path) if path else REPO_ROOT / "config" / "config.yaml"
    with open(cfg_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def read_hpo_terms(path: str | Path) -> list[str]:
    """Lee términos HP:XXXXXXX ignorando comentarios y etiquetas."""
    terms = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        token = line.split()[0]
        if token.startswith("HP:") and len(token) == 10:
            terms.append(token)
    return terms
