"""Stage 1: findings, splits and metrics."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from imle import checkpoint
from imle.agents.coding import render_findings
from imle.apply import apply_pending
from imle.findings import Effect, Evidence, Finding, finding_id
from imle.intervention import Action, Intervention, append
from imle.metrics import multiclass_log_loss
from imle.splits import carve, check_disjoint
from imle.state import SearchState
from imle.tree import Tree

AUTHORS = ["EAP", "HPL", "MWS"]


def sample_finding() -> Finding:
    return Finding.create("Char n-gram TF-IDF beats word counts.", [Evidence(node_id="n3", val_score=0.41,
                                                                            probe_score=0.43)],
                          step=5, effect="helps")


# --------------------------------------------------------------------------- findings


def test_finding_id_is_stable_and_order_free():
    assert finding_id("A  finding.", ["n2", "n1"]) == finding_id("a finding", ["n1", "n2", "n1"])
    assert finding_id("a finding", ["n1"]) != finding_id("a finding", ["n2"])
    assert finding_id("a finding", ["n1"]).startswith("f-")


def test_finding_dict_roundtrip_through_checkpoint(tmp_path: Path):
    f = sample_finding()
    checkpoint.write(tmp_path, 0, {"nodes": {}}, [f.to_dict()], {"current_node": None})
    stored = checkpoint.read(tmp_path)["findings"]
    assert stored == [f.to_dict()]
    assert Finding.from_dict(stored[0]) == f
    assert stored[0]["effect"] == "helps" and stored[0]["evidence"][0]["probe_score"] == 0.43


def test_old_finding_form_still_reads():
    f = Finding.from_dict({"id": "f1", "text": "x", "evidence": [{"node_id": "n3", "val_score": 0.41}]})
    assert f.effect == Effect.NEUTRAL and f.step == 0 and f.evidence[0].probe_score is None


def test_prompt_shows_val_but_not_probe():
    text = render_findings([sample_finding().to_dict()])
    assert "n3=0.41" in text and "0.43" not in text
    assert sample_finding().id in text


def test_correct_intervention_deletes_finding_dict(tmp_path: Path):
    f = sample_finding().to_dict()
    findings = [f]
    append(tmp_path / "queue.jsonl", Intervention(id="q1", ts="2026-10-24T00:00:00Z", source="human",
                                                  action=Action.CORRECT, target=f["id"]))
    records = apply_pending(tmp_path, Tree(), findings, SearchState())
    assert records[0].outcome == "applied" and findings == []


def test_dashboard_finding_access():
    """The dashboard lists finding IDs with finding.get("id") and shows each with st.write."""
    findings = [sample_finding().to_dict()]
    assert [x.get("id") for x in findings if x.get("id")] == [sample_finding().id]


# --------------------------------------------------------------------------- splits


def frame(n: int = 100) -> pd.DataFrame:
    return pd.DataFrame({"id": [f"r{i}" for i in range(n)], "label": [AUTHORS[i % 3] for i in range(n)]})


def test_carve_is_deterministic_and_sized():
    df = frame()
    a, b = carve(df, 0.2, 0.1, seed=3), carve(df, 0.2, 0.1, seed=3)
    assert a.equals(b)
    assert not a.equals(carve(df, 0.2, 0.1, seed=4))
    assert (a == "val").sum() == 20 and (a == "probe").sum() == 10
    check_disjoint(a, df["id"])


def test_carve_stratifies():
    df = frame(90)
    split = carve(df, 0.2, 0.1, seed=0, label="label")
    counts = pd.crosstab(df["label"], split)
    assert (counts["val"] == 6).all() and (counts["probe"] == 3).all()


def test_carve_rejects_bad_fractions():
    with pytest.raises(ValueError):
        carve(frame(), 0.6, 0.5)


def test_check_disjoint_catches_shared_ids():
    with pytest.raises(ValueError):
        check_disjoint(pd.Series(["train", "val"]), pd.Series(["r1", "r1"]))


# --------------------------------------------------------------------------- metrics


def truth(n: int = 6) -> pd.DataFrame:
    return pd.DataFrame({"id": range(n), "label": [AUTHORS[i % 3] for i in range(n)]})


def test_log_loss_known_values():
    t = truth()
    uniform = pd.DataFrame({"id": range(6), **{a: 1 / 3 for a in AUTHORS}})
    assert multiclass_log_loss(t, uniform) == pytest.approx(math.log(3))
    onehot = pd.DataFrame({"id": range(6), **{a: [float(l == a) for l in t["label"]] for a in AUTHORS}})
    assert multiclass_log_loss(t, onehot) == pytest.approx(0, abs=1e-12)
    wrong = pd.DataFrame({"id": range(6), **{a: [float(l != a) / 2 for l in t["label"]] for a in AUTHORS}})
    assert multiclass_log_loss(t, wrong) == pytest.approx(-math.log(1e-15 / (1 + 1e-15)), rel=1e-6)


def test_log_loss_renormalises_and_matches_ids_not_order():
    t = truth(3)
    pred = pd.DataFrame({"id": [2, 0, 1], "EAP": [2, 2, 2], "HPL": [2, 2, 2], "MWS": [4, 4, 4]})
    assert multiclass_log_loss(t, pred) == pytest.approx(-(2 * math.log(0.25) + math.log(0.5)) / 3)


def test_log_loss_configurable_columns():
    t = pd.DataFrame({"key": ["a", "b"], "y": ["x", "z"]})
    pred = pd.DataFrame({"key": ["a", "b"], "x": [0.5, 0.5], "z": [0.5, 0.5]})
    assert multiclass_log_loss(t, pred, id_col="key", label_col="y", classes=["x", "z"]) == pytest.approx(math.log(2))


@pytest.mark.parametrize("pred", [
    pd.DataFrame({"id": [0, 1], "EAP": [1, 1], "HPL": [0, 0]}),                     # missing column
    pd.DataFrame({"id": [0, 0, 1], "EAP": 1, "HPL": 0, "MWS": 0}),                 # duplicate id
    pd.DataFrame({"id": [0], "EAP": [1], "HPL": [0], "MWS": [0]}),                 # missing row
])
def test_log_loss_rejects_bad_predictions(pred):
    with pytest.raises(ValueError):
        multiclass_log_loss(truth(2), pred)


def test_log_loss_matches_stand_in_metric():
    pytest.importorskip("sklearn")
    from imle import stand_in_evaluation as ev

    rng = np.random.default_rng(0)
    t = truth(60)
    p = rng.dirichlet(np.ones(3), size=60)
    pred = pd.DataFrame({"id": range(60), **{a: p[:, i] for i, a in enumerate(AUTHORS)}})
    ours = multiclass_log_loss(t, pred)
    theirs = ev.metric(t.merge(pred, on="id"), {"kind": "multiclass", "targets": AUTHORS})
    assert ours == pytest.approx(theirs, rel=1e-9)
