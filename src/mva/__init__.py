"""MVA Hackathon 2026 – pipeline de priorización de variantes (Track 1).

Convención de zonas:
    data/, work/   -> ZONA ROJA: datos del paciente. Solo los lee el humano / los scripts locales.
    outputs/       -> ZONA VERDE: agregados validados por `mva-guard`. Puede verlos el LLM.
    fixtures/      -> datos sintéticos para tests.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
# Rutas a los datos e id de la muestra: van aquí y no en config.yaml, porque el repo se publica.
LOCAL_CONFIG = REPO_ROOT / "config" / "local.yaml"


def _merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for k, v in extra.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_config(path: str | Path | None = None) -> dict:
    """Carga config/config.yaml (o la ruta dada).

    Sin ruta explícita fusiona encima config/local.yaml si existe (fuera de git): rutas a los datos y
    guard.sample_ids.
    """
    cfg_path = Path(path) if path else REPO_ROOT / "config" / "config.yaml"
    with open(cfg_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if path is None and LOCAL_CONFIG.exists():
        with open(LOCAL_CONFIG, encoding="utf-8") as fh:
            cfg = _merge(cfg, yaml.safe_load(fh) or {})
    return cfg


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
