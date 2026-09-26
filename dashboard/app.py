"""Streamlit monitor.

Reads the latest checkpoint and appends interventions to the queue.
Never touches live agent state. Run with:

    streamlit run dashboard/app.py
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from imle import checkpoint
from imle.intervention import Action, Intervention, append

st.set_page_config(page_title="Interruptible MLE Agent", layout="wide")

runs_root = Path("runs")
run_ids = sorted(p.name for p in runs_root.iterdir() if p.is_dir()) if runs_root.exists() else []

with st.sidebar:
    st.header("Run")
    if not run_ids:
        st.info("No runs found in ./runs yet.")
        st.stop()
    run_id = st.selectbox("Run", run_ids, index=len(run_ids) - 1)
    run_dir = runs_root / run_id


@st.fragment(run_every=5)
def live_view() -> None:
    ck = checkpoint.read(run_dir)
    if ck is None:
        st.warning("No complete checkpoint yet.")
        return

    status = ck["status"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Checkpoint", ck["step"])
    c2.metric("Current node", status.get("current_node", "-"))
    c3.metric("Elapsed (s)", status.get("elapsed_s", "-"))

    nodes = pd.DataFrame(ck["tree"].get("nodes", {}).values())
    if nodes.empty:
        st.info("Tree is empty.")
        return

    # TODO: validation vs probe chart over time. The most important element on the page.
    st.subheader("Nodes")
    cols = [c for c in ["id", "parent_id", "operator", "status", "val_score", "probe_score", "plan"] if c in nodes]
    st.dataframe(nodes[cols], width="stretch", hide_index=True)

    st.subheader("Findings")
    for f in ck["findings"]:
        st.write(f)


live_view()

st.divider()
st.subheader("Intervene")
action = st.selectbox("Action", [a.value for a in Action])
target = st.text_input("Target (node or finding ID)")
note = st.text_input("Reason (optional)")
if st.button("Queue intervention"):
    item = Intervention(
        id=f"q-{uuid.uuid4().hex[:8]}",
        ts=datetime.now(timezone.utc).isoformat(),
        source="human",
        action=Action(action),
        target=target or None,
        note=note or None,
    )
    append(run_dir / "queue.jsonl", item)
    st.success(f"Queued {item.action.value} on {item.target}. Applies at the next safe point.")

# TODO: intervention history from applied.jsonl, including dropped actions.
# TODO: replay mode, a slider over all checkpoints of a finished run.
