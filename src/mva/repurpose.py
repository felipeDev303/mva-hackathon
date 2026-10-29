"""Track 2 · Reposicionamiento de fármacos desde el mecanismo de la enfermedad.

Usa solo datos públicos y el hallazgo a nivel de gen (nunca datos del paciente):

  1. red del gen semilla: socios en STRING (confianza ≥ string_min_score) + participantes de vías Reactome;
  2. fármacos por gen de la red: Open Targets (drugAndClinicalCandidates) y DGIdb (interacciones);
  3. dirección: con pérdida de función del gen semilla, inhibir un gen de rol `checkpoint` EMPEORA el defecto
     (lista "evitar") y activarlo es compatible; con un gen `checkpoint_target` (APC/C-CDC20) es al revés;
  4. ejes curados de literatura (config/track2.yaml), cada uno con PMID verificados;
  5. evidencia: aprobación (Open Targets APPROVAL o DGIdb approved), co-mención en PubMed con el mecanismo y PMID.

  6. "vigilar": fármacos fuera de la red con interacción plausible pero de dirección incierta (config `watch`).

Salidas (zona verde): outputs/track2_candidates.tsv, track2_avoid.tsv, track2_watch.tsv, track2_network.tsv,
track2_sources.json.

Uso:
    mva-repurpose                         # consulta las APIs (con caché en .cache/track2/)
    mva-repurpose --config config/track2.yaml --outputs outputs
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
import yaml

from mva import REPO_ROOT

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
DGIDB_URL = "https://dgidb.org/api/graphql"
STRING_URL = "https://string-db.org/api/json/interaction_partners"
REACTOME_URL = "https://reactome.org/ContentService/data/participants/{}/referenceEntities"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

INHIBITORY = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE ALLOSTERIC MODULATOR", "NEGATIVE MODULATOR",
              "INVERSE AGONIST", "DEGRADER", "DISRUPTING AGENT", "RELEASING AGENT INHIBITOR", "INHIBITORY"}
ACTIVATING = {"AGONIST", "ACTIVATOR", "POSITIVE ALLOSTERIC MODULATOR", "POSITIVE MODULATOR", "STABILISER",
              "PARTIAL AGONIST", "OPENER", "INDUCER", "ACTIVATING"}


# ───────────────────────── acceso a APIs (con caché) ─────────────────────────

class Http:
    """GET/POST JSON con caché en disco y reintentos. Los tests usan un doble con la misma interfaz."""

    def __init__(self, cache: Path | None = None, pause: float = 0.35, retries: int = 4):
        self.cache, self.pause, self.retries = cache, pause, retries
        if cache:
            cache.mkdir(parents=True, exist_ok=True)

    def _cached(self, key: str, fetch):
        path = self.cache / (hashlib.sha1(key.encode()).hexdigest() + ".json") if self.cache else None
        if path and path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        for attempt in range(self.retries):
            try:
                data = fetch()
                break
            except Exception:  # noqa: BLE001 — APIs públicas con caídas cortas
                if attempt == self.retries - 1:
                    raise
                time.sleep(2 * (attempt + 1))
        time.sleep(self.pause)
        if path:
            path.write_text(json.dumps(data), encoding="utf-8")
        return data

    def get_json(self, url: str):
        def fetch():
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "mva-repurpose"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        return self._cached("GET " + url, fetch)

    def post_json(self, url: str, payload: dict):
        body = json.dumps(payload).encode()

        def fetch():
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json",
                                                                   "User-Agent": "mva-repurpose"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        return self._cached("POST " + url + " " + body.decode(), fetch)


def string_partners(http, gene: str, min_score: int, limit: int) -> list[tuple[str, float]]:
    url = f"{STRING_URL}?identifiers={gene}&species=9606&required_score={min_score}&limit={limit}"
    return [(r["preferredName_B"], float(r["score"])) for r in http.get_json(url)]


def reactome_genes(http, pathway: str) -> set[str]:
    rows = http.get_json(REACTOME_URL.format(pathway))
    return {r["geneName"][0] for r in rows if r.get("databaseName") == "UniProt" and r.get("geneName")}


def ot_target_id(http, symbol: str) -> str | None:
    q = ('{ search(queryString: "%s", entityNames: ["target"], page: {index: 0, size: 5}) { hits { id name } } }'
         % symbol)
    hits = http.post_json(OT_URL, {"query": q})["data"]["search"]["hits"]
    return next((h["id"] for h in hits if h["name"] == symbol), None)


def _moa(drug: dict) -> tuple[list[str], str]:
    rows = (drug.get("mechanismsOfAction") or {}).get("rows") or []
    return sorted({(r.get("actionType") or "").upper() for r in rows if r.get("actionType")}), \
        "; ".join(sorted({r.get("mechanismOfAction") or "" for r in rows}))


def ot_target_drugs(http, ensembl_id: str) -> list[dict]:
    q = ('{ target(ensemblId: "%s") { drugAndClinicalCandidates { rows { maxClinicalStage drug { id name '
         'maximumClinicalStage mechanismsOfAction { rows { actionType mechanismOfAction targets { approvedSymbol } } } '
         '} } } } }' % ensembl_id)
    target = http.post_json(OT_URL, {"query": q})["data"]["target"] or {}
    out = []
    for row in (target.get("drugAndClinicalCandidates") or {}).get("rows") or []:
        d = row["drug"]
        actions, moa = _moa(d)
        out.append(dict(drug=d["name"].upper(), chembl_id=d["id"], stage=d.get("maximumClinicalStage") or "",
                        actions=actions, moa=moa))
    return out


def ot_drug(http, name: str) -> dict | None:
    q = ('{ search(queryString: "%s", entityNames: ["drug"], page: {index: 0, size: 5}) { hits { id name object { '
         '... on Drug { maximumClinicalStage mechanismsOfAction { rows { actionType mechanismOfAction } } } } } } }'
         % name.lower())
    hits = http.post_json(OT_URL, {"query": q})["data"]["search"]["hits"]
    hit = next((h for h in hits if h["name"].upper() == name.upper()), None)
    if not hit:
        return None
    actions, moa = _moa(hit["object"] or {})
    return dict(drug=hit["name"].upper(), chembl_id=hit["id"], stage=(hit["object"] or {}).get("maximumClinicalStage")
                or "", actions=actions, moa=moa)


def dgidb_interactions(http, genes: list[str]) -> list[dict]:
    q = ('{ genes(names: %s) { nodes { name interactions { drug { name approved } interactionTypes '
         '{ type directionality } } } } }' % json.dumps(genes))
    nodes = http.post_json(DGIDB_URL, {"query": q})["data"]["genes"]["nodes"]
    out = []
    for n in nodes:
        for it in n.get("interactions") or []:
            types = it.get("interactionTypes") or []
            out.append(dict(gene=n["name"], drug=it["drug"]["name"].upper(), approved=bool(it["drug"]["approved"]),
                            actions=sorted({(t.get("type") or "").upper() for t in types if t.get("type")}
                                           | {(t.get("directionality") or "").upper() for t in types
                                              if t.get("directionality")})))
    return out


def pubmed_count(http, term: str) -> int:
    url = EUTILS + "esearch.fcgi?db=pubmed&retmode=json&retmax=0&term=" + urllib.parse.quote(term)
    return int(http.get_json(url)["esearchresult"]["count"])


def pubmed_summaries(http, pmids: list[int]) -> dict[int, dict]:
    if not pmids:
        return {}
    url = EUTILS + "esummary.fcgi?db=pubmed&retmode=json&id=" + ",".join(map(str, sorted(set(pmids))))
    res = http.get_json(url)["result"]
    return {int(u): dict(title=res[u].get("title", ""), year=res[u].get("pubdate", "")[:4],
                         journal=res[u].get("source", "")) for u in res.get("uids", []) if "error" not in res[u]}


# ───────────────────────── reglas ─────────────────────────

def direction(actions: list[str]) -> str:
    acts = set(actions)
    if acts & INHIBITORY:
        return "inhibits"
    if acts & ACTIVATING:
        return "activates"
    return "unknown"


def classify(role: str, actions: list[str]) -> str:
    """compatible / avoid / uncertain para un gen semilla con pérdida de función."""
    d = direction(actions)
    if role == "checkpoint":
        return {"inhibits": "avoid", "activates": "compatible"}.get(d, "uncertain")
    if role == "checkpoint_target":
        return {"inhibits": "compatible", "activates": "avoid"}.get(d, "uncertain")
    return "uncertain"


def is_approved(stage: str = "", dgidb_approved: bool = False) -> bool:
    return stage.upper() in {"APPROVAL", "PHASE_4"} or dgidb_approved


def evidence_score(approved: bool, proximity: float, verified_pmids: int, pubmed_hits: int) -> float:
    """0–1, transparente:
    aprobación 0,3 · proximidad mecanística 0,3 (alelo 1,0 > nivel de proteína > vía > consecuencia > cáncer)
    · fuentes verificadas 0,2 (satura en 2 PMID) · co-mención en PubMed 0,2 (escala log, satura en ~100)."""
    return round(0.3 * approved + 0.3 * proximity + 0.2 * min(1.0, verified_pmids / 2)
                 + 0.2 * min(1.0, math.log10(1 + pubmed_hits) / 2), 3)


def regulatory(cfg: dict, drug: str, approved: bool) -> tuple[bool, str]:
    """Corrige la aprobación con la tabla regulatoria de la config (p. ej. suplementos, autorizaciones no renovadas)."""
    reg = (cfg.get("regulatory") or {}).get(drug.upper())
    if not reg:
        return approved, ""
    return bool(reg.get("approved", approved)), reg.get("note", "")


# ───────────────────────── pipeline ─────────────────────────

def build_network(http, cfg: dict) -> pd.DataFrame:
    seed, net, roles = cfg["seed"]["gene"], cfg["network"], cfg["roles"]
    rows = {seed: dict(gene=seed, string_score=1.0, in_reactome=False)}
    for g, s in string_partners(http, seed, net["string_min_score"], net["string_limit"]):
        rows[g] = dict(gene=g, string_score=s, in_reactome=False)
    for pw in net.get("reactome_pathways", []):
        for g in reactome_genes(http, pw):
            rows.setdefault(g, dict(gene=g, string_score=None, in_reactome=False))["in_reactome"] = True
    df = pd.DataFrame(rows.values())
    role_of = {g: r for r, genes in roles.items() for g in genes}
    df["role"] = df["gene"].map(role_of).fillna("other")
    return df.sort_values(["role", "gene"]).reset_index(drop=True)


def network_drugs(http, network: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, g in network.iterrows():
        ensg = ot_target_id(http, g["gene"])
        for d in ot_target_drugs(http, ensg) if ensg else []:
            rows.append(dict(gene=g["gene"], role=g["role"], source="open_targets", **d, dgidb_approved=False))
    for it in dgidb_interactions(http, network["gene"].tolist()):
        role = network.loc[network["gene"] == it["gene"], "role"]
        rows.append(dict(gene=it["gene"], role=role.iloc[0] if len(role) else "other", source="dgidb",
                         drug=it["drug"], chembl_id="", stage="", actions=it["actions"], moa="",
                         dgidb_approved=it["approved"]))
    if not rows:
        return pd.DataFrame(columns=["gene", "role", "source", "drug", "chembl_id", "stage", "actions", "moa",
                                     "dgidb_approved", "class", "approved"])
    df = pd.DataFrame(rows)
    df["class"] = [classify(r, a) for r, a in zip(df["role"], df["actions"])]
    df["approved"] = [is_approved(s, a) for s, a in zip(df["stage"], df["dgidb_approved"])]
    return df


def run(cfg: dict, http, outputs: Path) -> dict:
    network = build_network(http, cfg)
    drugs = network_drugs(http, network)
    mech_term = cfg["pubmed"]["mechanism_term"]

    all_pmids = (list(cfg["seed"].get("mechanism_pmids", [])) + [p for a in cfg["axes"] for p in a.get("pmids", [])]
                 + [p for w in cfg.get("watch", []) for p in w.get("pmids", [])])
    sources = pubmed_summaries(http, all_pmids)

    cands = []
    # Ejes curados
    for ax in cfg["axes"]:
        verified = [p for p in ax.get("pmids", []) if p in sources]
        for name in ax.get("drugs", []):
            d = ot_drug(http, name) or dict(drug=name.upper(), chembl_id="", stage="", actions=[], moa="")
            hits = pubmed_count(http, f'"{name.lower()}"[tiab] AND {ax["pubmed_term"]}')
            approved, reg_note = regulatory(cfg, name, is_approved(d["stage"]))
            notes = "; ".join(n for n in ((ax.get("notes") or {}).get(name, ""), reg_note) if n)
            cands.append(dict(drug=d["drug"], chembl_id=d["chembl_id"], source=f"axis:{ax['id']}", axis=ax["label"],
                              proximity=ax["proximity"], approved=approved, stage=d["stage"],
                              mechanism_of_action=d["moa"], pubmed_hits=hits, verified_pmids=";".join(map(str, verified)),
                              score=evidence_score(approved, ax["proximity"], len(verified), hits), notes=notes))
    # Fármacos aprobados y compatibles que salen de la red
    prox_net = float(cfg["network"].get("proximity", 0.7))
    compat = drugs[(drugs["class"] == "compatible") & drugs["approved"]] if len(drugs) else drugs
    for name, grp in compat.groupby("drug") if len(compat) else []:
        hits = pubmed_count(http, f'"{name.lower()}"[tiab] AND {mech_term}')
        first = grp.iloc[0]
        approved, reg_note = regulatory(cfg, name, True)
        cands.append(dict(drug=name, chembl_id=first["chembl_id"], source="network:" + ",".join(sorted(grp["gene"].unique())),
                          axis="Red del gen semilla (dirección compatible)", proximity=prox_net, approved=approved,
                          stage=first["stage"], mechanism_of_action=first["moa"], pubmed_hits=hits, verified_pmids="",
                          score=evidence_score(approved, prox_net, 0, hits), notes=reg_note))
    cand_df = pd.DataFrame(cands).sort_values(["score", "pubmed_hits"], ascending=False).reset_index(drop=True)

    # Vigilar: fármacos fuera de la red con interacción plausible pero de dirección incierta (p. ej. venenos del huso)
    watch = []
    for w in cfg.get("watch", []):
        verified = [p for p in w.get("pmids", []) if p in sources]
        for name in w.get("drugs", []):
            d = ot_drug(http, name) or dict(drug=name.upper(), chembl_id="", stage="", actions=[], moa="")
            watch.append(dict(drug=d["drug"], chembl_id=d["chembl_id"], group=w["label"], stage=d["stage"],
                              mechanism_of_action=d["moa"], rationale=w["rationale"].strip(),
                              verified_pmids=";".join(map(str, verified))))
    watch_df = pd.DataFrame(watch, columns=["drug", "chembl_id", "group", "stage", "mechanism_of_action", "rationale",
                                            "verified_pmids"])

    avoid = drugs[drugs["class"] == "avoid"] if len(drugs) else drugs
    if len(avoid):
        avoid = (avoid.assign(actions=avoid["actions"].map(";".join))
                 .sort_values(["approved", "stage"], ascending=False)
                 .drop_duplicates(["drug", "gene"])[["drug", "gene", "role", "actions", "stage", "approved", "moa",
                                                      "source"]])

    outputs.mkdir(parents=True, exist_ok=True)
    network.to_csv(outputs / "track2_network.tsv", sep="\t", index=False)
    cand_df.to_csv(outputs / "track2_candidates.tsv", sep="\t", index=False)
    watch_df.to_csv(outputs / "track2_watch.tsv", sep="\t", index=False)
    (avoid if len(avoid) else pd.DataFrame(columns=["drug", "gene"])).to_csv(outputs / "track2_avoid.tsv", sep="\t",
                                                                            index=False)
    (outputs / "track2_sources.json").write_text(json.dumps({str(k): v for k, v in sources.items()}, indent=2,
                                                            ensure_ascii=False), encoding="utf-8")
    summary = dict(network_genes=int(len(network)),
                   roles={k: int(v) for k, v in network["role"].value_counts().items()},
                   drug_target_pairs=int(len(drugs)),
                   network_compatible_approved=int(len(compat)) if len(drugs) else 0,
                   candidates=int(len(cand_df)), avoid_pairs=int(len(avoid)), watch=int(len(watch_df)),
                   pmids_requested=len(set(all_pmids)), pmids_verified=len(sources))
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=REPO_ROOT / "config" / "track2.yaml")
    ap.add_argument("--outputs", type=Path, default=REPO_ROOT / "outputs")
    ap.add_argument("--cache", type=Path, default=REPO_ROOT / ".cache" / "track2")
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    summary = run(cfg, Http(cache=args.cache), args.outputs)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
