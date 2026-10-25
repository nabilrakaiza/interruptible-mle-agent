"""Streamlit monitor.

Reads the latest checkpoint and appends interventions to the queue.
Never touches live agent state. Run with:

    streamlit run dashboard/app.py

Live mode follows a running run and refreshes every few seconds; interventions are
queued and apply at the agent's next safe point. Replay mode steps through every saved
checkpoint of a run, read only. Test scores stay hidden unless the run is finished and
"show test scores" is on. What a person does on a running run is logged to
dashboard_log.jsonl in its folder, for C6's interaction cost; finished runs are not touched.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from imle import monitor
from imle.intervention import Action

REFRESH_S = 5
SPLIT_COLOURS = {"validation": "#1f77b4", "probe": "#ff7f0e", "test": "#2ca02c"}

st.set_page_config(page_title="Interruptible MLE Agent", layout="wide")
if "session" not in st.session_state:
    st.session_state.session = uuid.uuid4().hex[:8]
    st.session_state.logged_runs = set()
    st.session_state.viewed = {}
SESSION = st.session_state.session


def score_chart(nodes: pd.DataFrame, best: pd.DataFrame, marks: pd.DataFrame, higher_is_better: bool) -> alt.Chart:
    """Validation vs probe over the run: every node as a faint point, the best-so-far node's scores as lines."""
    points = monitor.long_scores(nodes[[c for c in nodes.columns if c not in ("error", "script_path")]])
    points["plan"] = points["plan"].fillna("").str.slice(0, 160)
    lines = monitor.long_scores(best)
    x = alt.X("order:Q", title="node (creation order)")
    y = alt.Y("score:Q", title=f"score ({'higher' if higher_is_better else 'lower'} is better)",
              scale=alt.Scale(zero=False, domain=monitor.score_range(points["score"], lines["score"])))
    splits = [s for s in SPLIT_COLOURS if s in set(points["split"])]
    colour = alt.Color("split:N", title=None,
                       scale=alt.Scale(domain=splits, range=[SPLIT_COLOURS[s] for s in splits]))
    layers = [
        alt.Chart(points).mark_circle(size=28, clip=True).encode(
            x=x, y=y, color=colour,
            opacity=alt.condition(alt.datum.status == "pruned", alt.value(0.15), alt.value(0.45)),
            tooltip=["id", "operator", "status", "split", alt.Tooltip("score:Q", format=".5f"), "plan"]),
        alt.Chart(lines).mark_line(interpolate="step-after", strokeWidth=2.5).encode(
            x=x, y=y, color=colour,
            tooltip=[alt.Tooltip("best_node", title="best by validation"), "split",
                     alt.Tooltip("score:Q", format=".5f")]),
    ]
    if not marks.empty:
        layers.append(alt.Chart(marks).mark_rule(strokeDash=[4, 3], color="#8e24aa").encode(
            x="order:Q", tooltip=["action", "target", "source", "note"]))
    return alt.layer(*layers).properties(height=360)


def header(ck: dict, nodes: pd.DataFrame, best: pd.DataFrame) -> None:
    """The run's identity and its headline numbers."""
    status = ck["status"]
    st.caption(f"{status.get('task', '?')} · condition {status.get('condition', '?')} · seed {status.get('seed', '?')}"
               f" · checkpoint {ck['step']}" + (" · finished" if status.get("done") else ""))
    counts = nodes["status"].value_counts()
    c = st.columns(5)
    c[0].metric("Nodes", len(nodes), help="working / buggy / pruned: "
                f"{counts.get('working', 0)} / {counts.get('buggy', 0)} / {counts.get('pruned', 0)}")
    c[1].metric("Elapsed", f"{status.get('elapsed_s', 0) / 60:.0f} min")
    c[2].metric("Remaining", f"{max(status.get('remaining_s', 0) or 0, 0) / 60:.0f} min")
    if best.empty:
        return
    last = best.iloc[-1]
    c[3].metric(f"Best validation ({last['best_node']})", f"{last['val_score']:.5f}")
    gap = (last["probe_score"] - last["val_score"]) if pd.notna(last["probe_score"]) else None
    c[4].metric("Its probe", f"{last['probe_score']:.5f}" if gap is not None else "-",
                delta=f"{gap:+.5f} vs validation" if gap is not None else None, delta_color="off")


def node_tab(run_dir: Path, ck: dict, nodes: pd.DataFrame, best: pd.DataFrame, can_act: bool) -> None:
    """One node's details, and the actions a person can take on it."""
    ids = nodes["id"].tolist()
    default = ck["status"].get("final_node") or (best.iloc[-1]["best_node"] if not best.empty else ids[-1])
    key = f"node::{run_dir}"
    node_id = st.selectbox("Node", ids, index=ids.index(default) if default in ids else len(ids) - 1, key=key)
    if can_act and st.session_state.viewed.get(key) != node_id:
        st.session_state.viewed[key] = node_id
        monitor.log_event(run_dir, SESSION, "view_node", node=node_id, step=ck["step"])
    n = nodes.set_index("id").loc[node_id]
    cols = st.columns(4)
    cols[0].metric("Status", n["status"])
    cols[1].metric("Operator", n["operator"])
    cols[2].metric("Validation", f"{n['val_score']:.5f}" if pd.notna(n["val_score"]) else "-")
    cols[3].metric("Probe", f"{n['probe_score']:.5f}" if pd.notna(n["probe_score"]) else "-")
    st.write(f"**Parent:** {n['parent_id'] or '-'}  ")
    st.write(f"**Plan:** {n['plan'] or '-'}")
    if pd.notna(n["error"]) and n["error"]:
        st.error(n["error"])
    files = monitor.node_files(run_dir, node_id)
    with st.expander("Script"):
        st.code(files["script"] or "(no script)", language="python")
    with st.expander("stdout / stderr (end)"):
        st.text(files["stdout"] or "(empty stdout)")
        st.text(files["stderr"] or "(empty stderr)")

    choices = monitor.node_actions(n["status"], bool(n["script_path"]))
    if not choices:
        st.caption(f"No action applies to a {n['status']} node.")
        return
    with st.form(f"act::{run_dir}", clear_on_submit=True):
        choice = st.radio("Action on this node", choices, horizontal=True)
        note = st.text_input("Why (kept for the analysis)")
        if st.form_submit_button("Queue", disabled=not can_act):
            action, params = monitor.NODE_ACTIONS[choice]
            item = monitor.queue_intervention(run_dir, action, node_id, params, note, session=SESSION)
            st.success(f"Queued {item.action.value} on {node_id}. It applies at the next safe point.")


def findings_tab(run_dir: Path, ck: dict, can_act: bool) -> None:
    """The agent's findings, each with a form to delete or replace it."""
    findings = ck["findings"]
    if not findings:
        st.info("No findings yet (A4 off, or none written so far).")
        return
    for f in findings:
        with st.container(border=True):
            st.write(f"**{f.get('id', '?')}**: {f.get('text', f)}")
            evidence = f.get("evidence") or []
            if evidence:
                st.caption("Evidence: " + ", ".join(f"{e.get('node_id')} (val {e.get('val_score')})"
                                                    for e in evidence if isinstance(e, dict)))
            with st.form(f"correct::{run_dir}::{f.get('id')}", clear_on_submit=True):
                replacement = st.text_input("Replacement text (leave empty to delete)")
                note = st.text_input("Why")
                if st.form_submit_button("Correct", disabled=not can_act):
                    params = {"replacement": replacement} if replacement else {}
                    monitor.queue_intervention(run_dir, Action.CORRECT, f.get("id"), params, note, session=SESSION)
                    st.success("Queued.")


def intervene_tab(run_dir: Path, hist: pd.DataFrame, can_act: bool) -> None:
    """Run-wide actions (new draft, inject a card, change the budget) and the intervention history."""
    left, mid, right = st.columns(3)
    with left.form(f"draft::{run_dir}", clear_on_submit=True):
        st.write("**Start a fresh draft next**")
        note = st.text_input("Why", key=f"draft_note::{run_dir}")
        if st.form_submit_button("Queue draft", disabled=not can_act):
            monitor.queue_intervention(run_dir, Action.REDIRECT, None, {"operator": "draft"}, note, session=SESSION)
            st.success("Queued.")
    with mid.form(f"inject::{run_dir}", clear_on_submit=True):
        st.write("**Inject an approach or model card**")
        card = st.text_area("Text shown to the coding agent in every later prompt")
        if st.form_submit_button("Queue inject", disabled=not can_act) and card.strip():
            monitor.queue_intervention(run_dir, Action.INJECT, None, {"card": card.strip()}, session=SESSION)
            st.success("Queued.")
    with right.form(f"rebudget::{run_dir}", clear_on_submit=True):
        st.write("**Change the budget**")
        minutes = st.number_input("Minutes to add (negative to remove)", value=0, step=5)
        if st.form_submit_button("Queue rebudget", disabled=not can_act) and minutes:
            monitor.queue_intervention(run_dir, Action.REBUDGET, None, {"seconds": minutes * 60}, session=SESSION)
            st.success("Queued.")

    st.subheader("History")
    if hist.empty:
        st.caption("No interventions yet.")
    else:
        st.dataframe(hist.drop(columns=["id"]), width="stretch", hide_index=True)


def view(run_dir: Path, step: int | None, show_test: bool, live: bool) -> None:
    """The whole page for one checkpoint (the newest one in live mode)."""
    ck = monitor.read_step(run_dir, step)
    if ck is None:
        st.warning("No complete checkpoint yet.")
        return
    done = bool(ck["status"].get("done"))
    can_act = live and not done
    nodes = monitor.node_frame(ck, show_test=show_test and done)
    if nodes.empty:
        header(ck, nodes.assign(status=pd.Series(dtype=str)), pd.DataFrame())
        st.info("Tree is empty.")
        return
    hib = ck["tree"].get("higher_is_better", True)
    best = monitor.best_so_far(nodes, hib)
    header(ck, nodes, best)
    hist = monitor.history(run_dir)
    if not live:  # replay shows the interventions as they stood at this checkpoint
        hist = monitor.history_at(hist, ck["status"].get("timestamp"))
    marks = monitor.intervention_positions(hist, nodes)
    st.altair_chart(score_chart(nodes, best, marks, hib), width="stretch")
    st.caption("Lines: the node the agent would submit now (best by validation) and its probe score. "
               "Points: every node. Dashed lines: applied interventions.")
    if not can_act:
        st.caption("Read only: " + ("the run has finished." if done else "replay mode."))

    tree, node, findings, act = st.tabs(["Tree", "Node", "Findings", "Interventions"])
    with tree:
        st.graphviz_chart(monitor.tree_dot(nodes, final=ck["status"].get("final_node")), width="stretch")
    with node:
        node_tab(run_dir, ck, nodes, best, can_act)
    with findings:
        findings_tab(run_dir, ck, can_act)
    with act:
        intervene_tab(run_dir, hist, can_act)


with st.sidebar:
    st.header("Run")
    root = Path(st.text_input("Runs folder", "runs"))
    runs = monitor.find_runs(root)
    if not runs:
        st.info(f"No runs found in {root} yet.")
        st.stop()
    labels = [str(r.relative_to(root)) for r in runs]
    newest = max(range(len(runs)), key=lambda i: monitor.last_update(runs[i]))
    run_dir = runs[labels.index(st.selectbox("Run", labels, index=newest,
                                             help="Opens on the most recently updated run"))]
    latest = monitor.read_step(run_dir)
    finished = bool(latest and latest["status"].get("done"))
    if not finished and run_dir not in st.session_state.logged_runs:  # C6 logs live runs only
        st.session_state.logged_runs.add(run_dir)
        monitor.log_event(run_dir, SESSION, "session_start")
    mode = st.radio("View", ["Live", "Replay"], horizontal=True)
    steps = monitor.complete_steps(run_dir)
    step = None
    if mode == "Replay" and steps:
        step = st.select_slider("Checkpoint", steps, value=steps[-1])
    show_test = st.toggle("Show test scores", disabled=not finished,
                          help="Only for finished runs. No monitor sees test scores during a run.")

if mode == "Live":
    st.fragment(run_every=REFRESH_S)(view)(run_dir, None, show_test, True)
else:
    view(run_dir, step, show_test, False)
