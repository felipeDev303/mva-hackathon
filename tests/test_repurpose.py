"""Tests offline del Track 2: un doble de Http responde con formas reales (STRING, Reactome, Open Targets, DGIdb,
PubMed) pero con datos inventados. No hay red en `make test`."""

import json
import re

import pandas as pd
import yaml

from mva import REPO_ROOT
from mva.guard import run as guard_run
from mva.repurpose import classify, direction, evidence_score, is_approved, run

CFG = yaml.safe_load((REPO_ROOT / "config" / "track2.yaml").read_text(encoding="utf-8"))

# Fármacos inventados por gen (formato de Open Targets drugAndClinicalCandidates)
TARGET_DRUGS = {
    "MAD2L1": [("SYNTHINIB", "APPROVAL", "INHIBITOR")],      # checkpoint + inhibidor → evitar
    "CDC20": [("APCSTAT", "APPROVAL", "INHIBITOR")],         # diana del checkpoint + inhibidor → compatible
    "TTK": [("TTKIB", "PHASE_2", "INHIBITOR")],              # checkpoint + inhibidor en ensayo → evitar
}


class FakeHttp:
    def __init__(self):
        self.calls = []

    def get_json(self, url):
        self.calls.append(url)
        if "string-db.org" in url:
            return [{"preferredName_B": "MAD2L1", "score": 0.999}, {"preferredName_B": "CDC20", "score": 0.999}]
        if "reactome.org" in url:
            return [{"databaseName": "UniProt", "geneName": ["TTK"]}, {"databaseName": "ChEBI", "name": ["ATP"]}]
        if "esearch.fcgi" in url:
            return {"esearchresult": {"count": "12"}}
        if "esummary.fcgi" in url:
            ids = re.search(r"id=([\d,]+)", url).group(1).split(",")
            known = [i for i in ids if i != "39490401"]          # uno "no verificable"
            return {"result": {"uids": known, **{i: {"title": f"Paper {i}", "pubdate": "2011", "source": "J"}
                                                 for i in known}}}
        raise AssertionError(f"GET inesperado: {url}")

    def post_json(self, url, payload):
        q = payload["query"]
        self.calls.append(q)
        if "dgidb.org" in url:
            return {"data": {"genes": {"nodes": [{"name": "CDC20", "interactions": [
                {"drug": {"name": "apcstat", "approved": True},
                 "interactionTypes": [{"type": "inhibitor", "directionality": "INHIBITORY"}]}]}]}}}
        if 'entityNames: ["target"]' in q:
            sym = re.search(r'queryString: "([^"]+)"', q).group(1)
            return {"data": {"search": {"hits": [{"id": f"ENSG_{sym}", "name": sym}]}}}
        if "target(ensemblId:" in q:
            sym = re.search(r'ensemblId: "ENSG_([^"]+)"', q).group(1)
            rows = [{"maxClinicalStage": st, "drug": {"id": f"CHEMBL_{d}", "name": d, "maximumClinicalStage": st,
                     "mechanismsOfAction": {"rows": [{"actionType": act, "mechanismOfAction": f"{sym} {act.lower()}",
                                                      "targets": [{"approvedSymbol": sym}]}]}}}
                    for d, st, act in TARGET_DRUGS.get(sym, [])]
            return {"data": {"target": {"drugAndClinicalCandidates": {"rows": rows}}}}
        if 'entityNames: ["drug"]' in q:
            name = re.search(r'queryString: "([^"]+)"', q).group(1).upper()
            # Como la API real: también devuelve APPROVAL para la quercetina (fase histórica en ChEMBL)
            return {"data": {"search": {"hits": [{"id": f"CHEMBL_{name}", "name": name, "object": {
                "maximumClinicalStage": "APPROVAL",
                "mechanismsOfAction": {"rows": [{"actionType": "INHIBITOR", "mechanismOfAction": "x"}]}}}]}}}
        raise AssertionError(f"POST inesperado: {q[:80]}")


def test_direction_rules_follow_gene_role():
    assert direction(["INHIBITOR"]) == "inhibits" and direction(["AGONIST"]) == "activates"
    assert classify("checkpoint", ["INHIBITOR"]) == "avoid"
    assert classify("checkpoint", ["ACTIVATOR"]) == "compatible"
    assert classify("checkpoint_target", ["INHIBITOR"]) == "compatible"
    assert classify("checkpoint_target", ["AGONIST"]) == "avoid"
    assert classify("other", ["INHIBITOR"]) == "uncertain"
    assert is_approved("APPROVAL") and not is_approved("PHASE_2") and is_approved("", dgidb_approved=True)


def test_evidence_score_is_bounded_and_monotonic():
    assert evidence_score(False, 0.0, 0, 0) == 0.0
    assert evidence_score(True, 1.0, 5, 10_000) == 1.0
    assert evidence_score(True, 0.6, 1, 50) > evidence_score(True, 0.6, 1, 5)
    # A igual evidencia, actuar sobre el alelo pesa más que sobre la consecuencia aguas abajo
    assert evidence_score(True, 1.0, 1, 10) > evidence_score(True, 0.6, 1, 10)


def test_pipeline_end_to_end_offline(tmp_path):
    out = tmp_path / "outputs"
    summary = run(CFG, FakeHttp(), out)
    net = pd.read_csv(out / "track2_network.tsv", sep="\t")
    cand = pd.read_csv(out / "track2_candidates.tsv", sep="\t")
    avoid = pd.read_csv(out / "track2_avoid.tsv", sep="\t")

    assert set(net["gene"]) >= {"BUB1B", "MAD2L1", "CDC20", "TTK"}
    assert dict(zip(net["gene"], net["role"]))["CDC20"] == "checkpoint_target"
    # Ejes curados presentes; la tabla regulatoria corrige al suplemento aunque la API diga APPROVAL
    assert {"GENTAMICIN", "HYDROXYCHLOROQUINE", "DASATINIB"} <= set(cand["drug"])
    assert not cand.loc[cand["drug"] == "QUERCETIN", "approved"].iloc[0]
    assert "no renovada" in cand.loc[cand["drug"] == "ATALUREN", "notes"].iloc[0]
    # El eje alelo-dirigido (proximidad 1,0) queda por encima del eje de cáncer (0,5) a igual aprobación
    s = dict(zip(cand["drug"], cand["score"]))
    assert s["GENTAMICIN"] > s["HYDROXYCHLOROQUINE"]
    # Venenos del huso: no son candidatos, van a "vigilar"
    watch = pd.read_csv(out / "track2_watch.tsv", sep="\t")
    assert "VINCRISTINE" in set(watch["drug"]) and "VINCRISTINE" not in set(cand["drug"])
    # Inhibir la diana del checkpoint (APC/C-CDC20) entra como candidato compatible desde la red
    assert "APCSTAT" in set(cand["drug"])
    # Inhibir componentes del checkpoint va a "evitar", aprobado o en ensayo
    assert {"SYNTHINIB", "TTKIB"} <= set(avoid["drug"])
    assert cand["score"].is_monotonic_decreasing
    # Un PMID no verificable no cuenta como verificado
    assert summary["pmids_verified"] == summary["pmids_requested"] - 1
    assert json.loads((out / "track2_sources.json").read_text())


def test_track2_outputs_pass_guard(tmp_path, cfg):
    out = tmp_path / "outputs"
    run(CFG, FakeHttp(), out)
    assert not guard_run([out], cfg).errors
