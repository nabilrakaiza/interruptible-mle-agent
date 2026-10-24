
"""Streamlit dashboard for the Interruptible MLE Agent.

Features:
- Live checkpoint monitoring
- Validation vs probe performance chart
- Search tree node table
- Reflection findings
- Intervention history
- Historical checkpoint replay
- Human intervention queue

Run using:
    python -m streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from imle import checkpoint
from imle.intervention import Action, Intervention, append
import graphviz

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Interruptible MLE Agent",
    layout="wide",
)

st.title("Interruptible MLE Agent")
st.caption("Human-in-the-loop ML experimentation dashboard")


# --------------------------------------------------
# SELECT EXPERIMENT RUN
# --------------------------------------------------

runs_root = Path("runs")

run_ids = (
    sorted(p.name for p in runs_root.iterdir() if p.is_dir())
    if runs_root.exists()
    else []
)

with st.sidebar:
    st.header("Experiment Run")

    if not run_ids:
        st.info("No runs found in ./runs yet.")
        st.stop()

    run_id = st.selectbox(
        "Select Run",
        run_ids,
        index=len(run_ids) - 1,
    )

    run_dir = runs_root / run_id


# --------------------------------------------------
# REPLAY MODE
# --------------------------------------------------

replay_mode = st.toggle(
    "Replay historical checkpoints",
    value=False,
)

if replay_mode:
    st.info(
        "Replay mode is read-only. "
        "You can inspect previous checkpoints, "
        "but cannot submit interventions."
    )


# --------------------------------------------------
# TIMESTAMP HELPER
# --------------------------------------------------

def parse_timestamp(value):
    """Convert an ISO timestamp into a UTC datetime."""

    if not value:
        return None

    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except (ValueError, TypeError, AttributeError):
        return None


def display_search_tree(tree_data: dict):
    """Visualize ML experiments using parent-child relationships."""

    st.subheader("Search Tree Visualization")

    nodes = tree_data.get("nodes", {})

    if not nodes:
        st.info("No search nodes available.")
        return

    graph = graphviz.Digraph()

    graph.attr(rankdir="TB")
    graph.attr("node", shape="box", style="rounded,filled")

    status_colors = {
        "working": "#D1FAE5",
        "buggy": "#FEE2E2",
        "pruned": "#FED7AA",
        "running": "#DBEAFE",
        "abandoned": "#E5E7EB",
    }

    # Create nodes.
    for node_id, node in nodes.items():
        status = node.get("status", "running")

        val = node.get("val_score")
        probe = node.get("probe_score")

        val_text = f"{val:.3f}" if val is not None else "-"
        probe_text = f"{probe:.3f}" if probe is not None else "-"

        label = (
            f"{node_id}\n"
            f"{node.get('operator', '-')}\n"
            f"Val: {val_text} | Probe: {probe_text}"
        )

        graph.node(
            node_id,
            label=label,
            fillcolor=status_colors.get(status, "#FFFFFF"),
            fontcolor="#111827",
            color="#64748B",
        )

    # Connect parents to children.
    for node_id, node in nodes.items():
        parent_id = node.get("parent_id")

        if parent_id is not None and parent_id in nodes:
            graph.edge(parent_id, node_id)

    st.graphviz_chart(
        graph,
        width="stretch",
    )

    st.caption(
        "Green: working | Red: buggy | "
        "Orange: pruned | Blue: running | "
        "Grey: abandoned"
    )


def display_node_inspector(tree_data: dict):
    """Display detailed information about a selected node."""

    st.subheader("Node Inspector")

    nodes = tree_data.get("nodes", {})

    if not nodes:
        st.info("No nodes available.")
        return

    selected_id = st.selectbox(
        "Select a node to inspect",
        options=list(nodes.keys()),
    )

    node = nodes[selected_id]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Validation Score",
        node.get("val_score")
        if node.get("val_score") is not None
        else "-",
    )

    c2.metric(
        "Probe Score",
        node.get("probe_score")
        if node.get("probe_score") is not None
        else "-",
    )

    c3.metric(
        "Status",
        node.get("status", "-"),
    )

    st.write("**Parent:**", node.get("parent_id") or "Root")
    st.write("**Operator:**", node.get("operator", "-"))

    st.write("**Plan:**")
    st.write(node.get("plan") or "No plan recorded.")

    if node.get("error"):
        st.error(node["error"])

    st.write("**Script path:**", node.get("script_path") or "-")

# --------------------------------------------------
# INTERVENTION HISTORY
# --------------------------------------------------

def display_intervention_history(
    run_dir: Path,
    checkpoint_time=None,
    replay=False,
):
    """Display applied and dropped interventions."""

    st.subheader("Intervention History")

    applied_path = run_dir / "applied.jsonl"

    if not applied_path.exists():
        st.info("No interventions recorded yet.")
        return

    history = []

    for line in applied_path.read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Filter future interventions during replay.
        if replay:
            applied_time = parse_timestamp(
                record.get("applied_at")
            )

            selected_time = parse_timestamp(
                checkpoint_time
            )

            # If timestamps are unavailable, we cannot
            # reliably place this intervention in history.
            if applied_time is None or selected_time is None:
                continue

            if applied_time > selected_time:
                continue

        intervention = record.get("intervention", {})

        history.append({
            "Time": intervention.get("ts"),
            "Source": intervention.get("source"),
            "Action": intervention.get("action"),
            "Target": intervention.get("target"),
            "Outcome": record.get("outcome"),
            "Reason": record.get("reason"),
        })

    if history:
        st.dataframe(
            pd.DataFrame(history),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No interventions recorded by this checkpoint.")

def get_available_nodes(run_dir: Path):
    """Return selectable node IDs from the latest checkpoint."""

    ck = checkpoint.read(run_dir)

    if ck is None:
        return []

    nodes = ck["tree"].get("nodes", {})

    return [
        node_id
        for node_id, node in nodes.items()
        if node.get("status") == "working"
    ]
# --------------------------------------------------
# LIVE MONITOR AND REPLAY
# --------------------------------------------------

@st.fragment(run_every=5)
def live_view():

    checkpoints_dir = run_dir / "checkpoints"

    available_steps = (
        sorted(
            int(p.name)
            for p in checkpoints_dir.iterdir()
            if p.is_dir()
            and p.name.isdigit()
            and (p / "status.json").exists()
        )
        if checkpoints_dir.exists()
        else []
    )

    if not available_steps:
        st.warning("No complete checkpoints found.")
        return

    # Select checkpoint.
    if replay_mode:

        selected_step = st.select_slider(
            "Checkpoint",
            options=available_steps,
            value=available_steps[-1],
        )

    else:
        selected_step = available_steps[-1]

    ck = checkpoint.read(run_dir, selected_step)

    if ck is None:
        st.warning("Could not load checkpoint.")
        return

    status = ck["status"]

    # --------------------------------------------------
    # RUN METRICS
    # --------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Checkpoint",
        ck["step"],
    )

    c2.metric(
        "Current Node",
        status.get("current_node") or "-",
    )

    c3.metric(
        "Elapsed (s)",
        status.get("elapsed_s", "-"),
    )

    c4.metric(
        "Remaining (s)",
        status.get("remaining_s", "-"),
    )

    st.divider()

    # --------------------------------------------------
    # LOAD SEARCH TREE
    # --------------------------------------------------

    nodes = pd.DataFrame(
        ck["tree"].get("nodes", {}).values()
    )

    if nodes.empty:
        st.info("Search tree is empty.")
        display_intervention_history(
            run_dir,
            checkpoint_time=status.get("timestamp"),
            replay=replay_mode,
        )
        return

    # --------------------------------------------------
    # VALIDATION VS PROBE CHART
    # --------------------------------------------------

    st.subheader("Validation vs Probe Performance")
    higher_is_better = ck["tree"].get("higher_is_better", True)

    if higher_is_better:
        st.caption("Optimization direction: Higher scores are better.")
    else:
        st.caption("Optimization direction: Lower scores are better.")
    if {"id", "val_score", "probe_score"}.issubset(
        nodes.columns
    ):

        chart_data = nodes[
            ["id", "val_score", "probe_score"]
        ].copy()

        chart_data = chart_data.rename(
            columns={
                "val_score": "Validation",
                "probe_score": "Probe",
            }
        )

        chart_data = chart_data.set_index("id")

        st.line_chart(
            chart_data,
            x_label="Experiment Node",
            y_label="Score",
        )

        st.caption(
            "Scores are shown in node insertion order. "
            "This is not a visualization of tree branches."
        )

    else:
        st.info("Score data is not available.")

    # --------------------------------------------------
    # NODE TABLE
    # --------------------------------------------------
    display_search_tree(ck["tree"])
    display_node_inspector(ck["tree"])
    st.subheader("Search Tree Nodes")

    columns = [
        "id",
        "parent_id",
        "operator",
        "status",
        "val_score",
        "probe_score",
        "plan",
    ]

    available_columns = [
        col for col in columns if col in nodes.columns
    ]

    st.dataframe(
        nodes[available_columns],
        width="stretch",
        hide_index=True,
    )

    # --------------------------------------------------
    # FINDINGS
    # --------------------------------------------------

    st.subheader("Reflection Findings")

    findings = ck.get("findings", [])

    if findings:
        for finding in findings:
            st.write(finding)
    else:
        st.info("No findings recorded yet.")

    # --------------------------------------------------
    # INTERVENTION HISTORY
    # --------------------------------------------------

    display_intervention_history(
        run_dir,
        checkpoint_time=status.get("timestamp"),
        replay=replay_mode,
    )


live_view()



# --------------------------------------------------
# HUMAN INTERVENTIONS
# --------------------------------------------------

st.divider()
st.subheader("Human Intervention")

if replay_mode:
    st.info(
        "Interventions are disabled during replay. "
        "Switch to live mode to submit a request."
    )

# 1. SELECT ACTION

action = st.selectbox(
    "Action",
    [a.value for a in Action],
    disabled=replay_mode,
)


# 2. ACTION-SPECIFIC PARAMETERS

params = {}

if action == Action.REDIRECT.value:
    operator = st.selectbox(
        "Next operator",
        ["draft", "debug", "improve"],
        disabled=replay_mode,
    )
    params["operator"] = operator

elif action == Action.REBUDGET.value:
    seconds = st.number_input(
        "Budget adjustment (seconds)",
        value=0.0,
        disabled=replay_mode,
    )
    params["seconds"] = seconds

elif action == Action.INJECT.value:
    card = st.text_area(
        "Model card or suggested approach",
        disabled=replay_mode,
    )
    params["card"] = card

elif action == Action.CORRECT.value:
    replacement = st.text_area(
        "Replacement finding (leave empty to delete)",
        disabled=replay_mode,
    )
    if replacement.strip():
        params["replacement"] = replacement.strip()


# 3. LOAD LATEST CHECKPOINT

latest_ck = checkpoint.read(run_dir)
run_finished = (
    latest_ck is not None
    and latest_ck["status"].get("done", False)
)

all_nodes = (
    latest_ck["tree"].get("nodes", {})
    if latest_ck
    else {}
)

findings = latest_ck.get("findings", []) if latest_ck else []


# 4. DETERMINE ELIGIBLE TARGETS

target_options = []
requires_target = False

if action == Action.PRUNE.value:
    requires_target = True
    target_options = [
        node_id
        for node_id, node in all_nodes.items()
        if node.get("status") != "pruned"
    ]

elif action == Action.OVERRIDE.value:
    requires_target = True
    target_options = [
        node_id
        for node_id, node in all_nodes.items()
        if node.get("status") == "working"
    ]

elif action == Action.REDIRECT.value:
    operator = params.get("operator")

    if operator == "debug":
        requires_target = True
        target_options = [
            node_id
            for node_id, node in all_nodes.items()
            if node.get("status") == "buggy"
            and node.get("script_path")
        ]

    elif operator == "improve":
        requires_target = True
        target_options = [
            node_id
            for node_id, node in all_nodes.items()
            if node.get("status") == "working"
        ]

    # Draft does not require a target.

elif action == Action.CORRECT.value:
    requires_target = True
    target_options = [
        finding.get("id")
        for finding in findings
        if finding.get("id")
    ]


# 5. TARGET DROPDOWN

target = None

if requires_target:
    if target_options:
        target = st.selectbox(
            "Target",
            options=target_options,
            disabled=replay_mode,
        )
    else:
        st.warning("No eligible targets available.")

else:
    st.caption("This action does not require a target.")


# 6. OPTIONAL REASON

note = st.text_input(
    "Reason (optional)",
    disabled=replay_mode,
)


# 7. VALIDATE AND QUEUE INTERVENTION

if run_finished:
    st.warning(
        "This run has finished. "
        "New interventions cannot be submitted."
    )

if st.button(
    "Queue Intervention",
    disabled=(
        replay_mode
        or run_finished
        or (requires_target and not target_options)
    ),
):

    if requires_target and not target:
        st.error("Please select a valid target.")

    elif (
        action == Action.INJECT.value
        and not params.get("card", "").strip()
    ):
        st.error("Please enter a model card or approach.")

    elif (
        action == Action.REBUDGET.value
        and params.get("seconds", 0) == 0
    ):
        st.error("Budget adjustment cannot be zero.")

    else:
        item = Intervention(
            id=f"q-{uuid.uuid4().hex[:8]}",
            ts=datetime.now(timezone.utc).isoformat(),
            source="human",
            action=Action(action),
            target=target,
            params=params,
            note=note.strip() or None,
        )

        append(
            run_dir / "queue.jsonl",
            item,
        )

        st.success(
            f"Queued {item.action.value} "
            f"on {item.target or 'run'}. "
            "The controller will process it "
            "at the next safe point."
        )
