"""Annotated trajectories: one run told as a timeline, for role 2's report section.

The proposal (Section 5.3) promises at least two annotated trajectories, one where an
intervention helped and one where it did not. This script builds the raw material from a
saved run folder:

    trajectory.png  scores over the run: validation, probe, and test once graded, with the
                    operator of each node, crashes, interventions, the final pick and the
                    best node on the check score
    timeline.md     the key events in order, each with an automatic note: drafts, new bests,
                    exhausted improve chains, crashes and their fixes, overfitting and no-op
                    labels from the error taxonomy, first use of each model card, every
                    intervention, the final pick and the node that should have been picked

The "why it matters" commentary for the report is written by hand from these.

    python scripts/trajectory.py runs/<run>                   # writes into runs/<run>/trajectory/
    python scripts/trajectory.py runs/<run> --all             # list every node, not only key events
    python scripts/trajectory.py --pairs runs/                # intervened runs vs. their C1 twin
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from imle.controller import improve_chains, latest_complete_checkpoint
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("error_taxonomy", Path(__file__).with_name("error_taxonomy.py"))
taxonomy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(taxonomy)

# Estimator and transformer names in a card's recipe, used to spot the card's idea in a script.
_ESTIMATOR = re.compile(
    r"\b[A-Z][A-Za-z]*(?:Classifier|Regressor|Regression|Vectorizer|Transformer|Encoder|Scaler|NB|SVC|SVR|PCA)\b"
)


@dataclass
class Event:
    """One line of the timeline: the node it belongs to (None for run-level events), a kind and a note."""

    node: str | None
    kind: str
    note: str


@dataclass
class Run:
    """Everything the timeline needs from one run folder."""

    path: Path
    tree: Tree
    status: dict
    search: dict
    rows: dict[str, dict]          # error taxonomy row per node
    summary: dict                  # error taxonomy run summary
    applied: list[dict]            # applied.jsonl records
    cards: list[dict]              # model cards the run used


def load(run_dir: Path) -> Run:
    """Read a run folder: latest complete checkpoint, config, taxonomy labels, interventions and cards."""
    ck = latest_complete_checkpoint(run_dir)
    if ck is None:
        raise SystemExit(f"{run_dir} has no complete checkpoint")
    cfg_path = run_dir / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
    rows, summary = taxonomy.classify_run(run_dir)
    applied_path = run_dir / "applied.jsonl"
    applied = [json.loads(line) for line in applied_path.read_text().splitlines() if line.strip()] \
        if applied_path.exists() else []
    cards_path = run_dir / "model_cards.json"
    cards = json.loads(cards_path.read_text()).get("cards", []) if cards_path.exists() else []
    search = {"improve_min_rel_gain": 0.0, "improve_patience": 3, **(cfg.get("search") or {})}
    return Run(run_dir, Tree.model_validate(ck["tree"]), ck["status"], search,
               {r["node"]: r for r in rows}, summary, applied, cards)


def fmt(x: float | None) -> str:
    """A score with four decimals, or a dash."""
    return "-" if x is None else f"{x:.4f}"


def short(text: str, n: int = 110) -> str:
    """The first `n` characters of a plan on one line."""
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 3] + "..."


def better(tree: Tree, a: float, b: float) -> bool:
    """Whether score `a` is strictly better than `b` for this task's direction."""
    return a > b if tree.higher_is_better else a < b


def node_after(tree: Tree, when: str) -> str | None:
    """The last node that finished before the timestamp `when` (where an intervention landed)."""
    t = datetime.fromisoformat(when)
    done = [n for n in tree.nodes.values() if n.finished_at and datetime.fromisoformat(n.finished_at) <= t]
    return done[-1].id if done else None


def card_estimators(card: dict) -> list[str]:
    """Estimator names a card recommends, such as MLPClassifier or TfidfVectorizer."""
    return sorted(set(_ESTIMATOR.findall(f"{card.get('name', '')} {card.get('recipe', '')}")))


def events(run: Run, every_node: bool = False) -> list[Event]:
    """The annotated timeline of a run, in node order, then the run-level verdict."""
    tree, out = run.tree, []
    nodes = list(tree.nodes.values())
    patience = run.search["improve_patience"]
    best: Node | None = None
    exhausted: set[str] = set()
    card_seen: set[str] = set()
    interventions: dict[str | None, list[dict]] = {}
    for record in run.applied:
        interventions.setdefault(node_after(tree, record["applied_at"]), []).append(record)

    for record in interventions.get(None, []):
        out.append(intervention_event(None, record))
    for i, n in enumerate(nodes):
        row = run.rows.get(n.id, {})
        labels = [x for x in (row.get("labels") or "").split(",") if x]
        notes: list[Event] = []
        if n.operator == Operator.DRAFT:
            notes.append(Event(n.id, "draft", f"{short(n.plan)} (val {fmt(n.val_score)})"))
        if n.status == NodeStatus.BUGGY:
            kind = row.get("category", "error")
            detail = row.get("exception") or (n.error or "").split("\n")[0]
            notes.append(Event(n.id, "crash", f"{kind}: {short(detail, 140)}"))
        if n.operator == Operator.DEBUG and n.status == NodeStatus.WORKING:
            root, attempts = n, 0
            while root.operator == Operator.DEBUG and root.parent_id:
                root, attempts = tree.nodes[root.parent_id], attempts + 1
            notes.append(Event(n.id, "fixed", f"debug fixed the crash in {root.id} after {attempts} attempt(s)"))
        if n.status == NodeStatus.WORKING and n.val_score is not None and (best is None or better(tree, n.val_score, best.val_score)):
            gain = "" if best is None else f", {abs(n.val_score - best.val_score) / abs(best.val_score) * 100:.2f}% better than {best.id}"
            notes.append(Event(n.id, "new best", f"val {fmt(n.val_score)}, probe {fmt(n.probe_score)}{gain}: {short(n.plan, 90)}"))
            best = n
        if "validation_overfitting" in labels:
            parent = tree.nodes[n.parent_id]
            notes.append(Event(n.id, "overfitting", f"beat {parent.id} on validation ({fmt(parent.val_score)} -> "
                               f"{fmt(n.val_score)}) but got worse on {taxonomy.check_score(n)[1]} "
                               f"({fmt(taxonomy.check_score(parent)[0])} -> {fmt(taxonomy.check_score(n)[0])})"))
        if "no_change" in labels:
            notes.append(Event(n.id, "no-op", f"same predictions as {n.parent_id}: {short(n.plan, 90)}"))
        if script := _script(run.path, n):
            for card in run.cards:
                hit = [e for e in card_estimators(card) if e in script and card["name"] not in card_seen]
                if hit:
                    card_seen.add(card["name"])
                    notes.append(Event(n.id, "card used", f"first script with {', '.join(hit)} from the card "
                                       f"\"{card['name']}\""))
        chain, failed = improve_chains(Tree(higher_is_better=tree.higher_is_better,
                                            nodes={m.id: m for m in nodes[: i + 1]}), run.search)
        start = chain[n.id]
        if failed[start] >= patience and start not in exhausted:
            exhausted.add(start)
            # By default only the chain holding the best node so far: the search gives up its lead line.
            if every_node or (best is not None and chain.get(best.id) == start):
                notes.append(Event(n.id, "chain exhausted", f"the chain from {start} had {failed[start]} attempts "
                                   "without a real gain; the search moves elsewhere"))
        if every_node and not notes:
            notes.append(Event(n.id, n.operator.value, f"{short(n.plan, 90)} (val {fmt(n.val_score)})"))
        out += notes
        for record in interventions.get(n.id, []):
            out.append(intervention_event(n.id, record))
    return out + verdict(run)


def chains_exhausted(run: Run) -> int:
    """How many improve chains of the finished run reached improve_patience."""
    _, failed = improve_chains(run.tree, run.search)
    return sum(1 for count in failed.values() if count >= run.search["improve_patience"])


def intervention_event(after: str | None, record: dict) -> Event:
    """A timeline line for one applied or dropped intervention."""
    item = record["intervention"]
    target = f" {item['target']}" if item.get("target") else ""
    params = f" {json.dumps(item['params'])}" if item.get("params") else ""
    reason = f" ({record['reason']})" if record.get("reason") else ""
    note = f" - {item['note']}" if item.get("note") else ""
    return Event(after, "intervention", f"{item['source']}: {item['action']}{target}{params}, "
                 f"{record['outcome']}{reason}{note}")


def verdict(run: Run) -> list[Event]:
    """Run-level lines: why it stopped, the final pick, and the best node on the check score."""
    tree, status = run.tree, run.status
    out = [Event(None, "stop", f"{status.get('stop_reason') or 'not finished'}, final selection "
                 f"{status.get('final_selection') or '-'}")]
    working = [n for n in tree.nodes.values() if n.status == NodeStatus.WORKING and n.val_score is not None]
    final = tree.nodes.get(status.get("final_node") or "")
    if not working or final is None:
        return out
    checked = [(n, *taxonomy.check_score(n)) for n in working]
    basis = taxonomy.check_score(final)[1]
    scored = sorted(((n, s) for n, s, b in checked if s is not None and b == basis),
                    key=lambda x: x[1], reverse=tree.higher_is_better)
    by_val = sorted(working, key=lambda n: n.val_score, reverse=tree.higher_is_better)
    rank = {n.id: i for i, (n, _) in enumerate(scored, 1)}
    final_check = taxonomy.check_score(final)[0]
    out.append(Event(final.id, "final pick", f"val {fmt(final.val_score)} (rank {by_val.index(final) + 1} of "
                     f"{len(working)}), {basis} {fmt(final_check)} (rank {rank.get(final.id, '-')} of {len(scored)})"))
    if scored and scored[0][0].id != final.id:
        top = scored[0][0]
        out.append(Event(top.id, f"best on {basis}", f"{basis} {fmt(scored[0][1])}, but val rank "
                         f"{by_val.index(top) + 1} of {len(working)}: {short(top.plan, 90)}"))
    return out


def _script(run_dir: Path, node: Node) -> str:
    """A node's script text, or "" if it has none."""
    path = run_dir / node.script_path if node.script_path else None
    return path.read_text(errors="replace") if path and path.exists() else ""


def timeline_md(run: Run, evs: list[Event]) -> str:
    """The timeline as markdown: a header about the run, then one table row per event."""
    s, m = run.status, run.summary
    calls_path = run.path / "llm_calls.jsonl"
    calls = [json.loads(line) for line in calls_path.read_text().splitlines()] if calls_path.exists() else []
    tokens = sum(c.get("input_tokens", 0) + c.get("output_tokens", 0) for c in calls)
    lines = [
        f"# Trajectory: {run.path.name}",
        "",
        f"- **Task** {s.get('task')}, **condition** {s.get('condition')}, **seed** {s.get('seed')}",
        (f"- **Nodes** {len(run.tree.nodes)} ({m.get('working_rate', 0) * 100:.0f}% working), "
         f"**budget used** {s.get('elapsed_s', 0) / 60:.1f} min, **LLM** {len(calls)} calls, {tokens:,} tokens"),
        (f"- **Interventions** {sum(r['outcome'] == 'applied' for r in run.applied)} applied, "
         f"{sum(r['outcome'] != 'applied' for r in run.applied)} dropped"),
        f"- **Model cards** {', '.join(c['name'] for c in run.cards) or 'none recorded'}",
        (f"- **Search** {chains_exhausted(run)} improve chains exhausted; longest stretch without a new "
         f"best {m.get('longest_no_new_best')} nodes; selection regret {m.get('selection_regret')} on "
         f"{m.get('regret_basis') or '-'}"),
        "",
        "Lower scores are better." if not run.tree.higher_is_better else "Higher scores are better.",
        "",
        "| Node | Event | Note |",
        "|---|---|---|",
    ]
    lines += [f"| {e.node or ''} | {e.kind} | {e.note.replace('|', '/')} |" for e in evs]
    lines += ["", "## Annotations", "", ("(Written by hand for the report: what this run shows, and what an "
                                          "intervention did or could have done.)"), ""]
    return "\n".join(lines)


def plot(run: Run, evs: list[Event], path: Path) -> None:
    """Draw the score figure: one point per node, coloured by operator, with the key events marked."""
    import matplotlib
    import matplotlib.ticker

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tree = run.tree
    nodes = list(tree.nodes.values())
    index = {n.id: i for i, n in enumerate(nodes)}
    values = [v for n in nodes for v in (n.val_score, n.probe_score, n.test_score) if v is not None]
    if not values:
        return
    values.sort()
    lo, hi = values[0], values[min(len(values) - 1, int(0.95 * len(values)))]
    pad = (hi - lo) * 0.15 or 0.01
    top, bottom = hi + pad, lo - pad

    def clip(v: float) -> float:
        """Keep outliers on the chart, drawn at its edge."""
        return min(max(v, bottom), top)

    fig, ax = plt.subplots(figsize=(12, 5))
    colours = {Operator.DRAFT: "#1f77b4", Operator.IMPROVE: "#2ca02c", Operator.DEBUG: "#ff7f0e"}
    for op, colour in colours.items():
        xs = [index[n.id] for n in nodes if n.operator == op and n.val_score is not None]
        ys = [clip(n.val_score) for n in nodes if n.operator == op and n.val_score is not None]
        ax.scatter(xs, ys, s=22, color=colour, label=f"val ({op.value})", zorder=3)
    probe = [(index[n.id], clip(n.probe_score)) for n in nodes if n.probe_score is not None]
    if probe:
        ax.scatter(*zip(*probe), s=10, color="#999999", marker="s", label="probe", zorder=2)
    test = [(index[n.id], clip(n.test_score)) for n in nodes if n.test_score is not None]
    if test:
        ax.scatter(*zip(*test), s=14, color="black", marker="x", label="test", zorder=2)
    crashed = [index[n.id] for n in nodes if n.status == NodeStatus.BUGGY]
    if crashed:
        ax.scatter(crashed, [bottom] * len(crashed), marker="v", color="#d62728", s=30, label="crash", zorder=3)

    running, best = [], None
    for n in nodes:
        if n.status == NodeStatus.WORKING and n.val_score is not None and (best is None or better(tree, n.val_score, best)):
            best = n.val_score
        running.append(best)
    ax.step(range(len(nodes)), [clip(b) if b is not None else None for b in running], where="post",
            color="#2ca02c", alpha=0.5, label="best val so far")

    for e in evs:
        if e.node is None or e.node not in index:
            continue
        x, n = index[e.node], tree.nodes[e.node]
        if e.kind == "final pick":
            ax.scatter([x], [clip(n.val_score)], marker="*", s=260, color="gold", edgecolor="black", zorder=4,
                       label="final pick")
        elif e.kind.startswith("best on"):
            check = taxonomy.check_score(n)[0]
            ax.scatter([x], [clip(check)], marker="D", s=90, facecolor="none", edgecolor="purple", zorder=4,
                       label=e.kind)
        elif e.kind == "intervention":
            ax.axvline(x + 0.5, color="purple", linestyle="--", alpha=0.6)
            ax.annotate(e.note.split(",")[0].split(": ")[-1], (x + 0.5, top), rotation=90, fontsize=7,
                        va="top", ha="right", color="purple")
    ax.set_ylim(bottom - pad * 0.3, top + pad * 0.3)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.set_xlabel("node (creation order)")
    direction = "higher" if tree.higher_is_better else "lower"
    ax.set_ylabel(f"score ({direction} is better; outliers drawn at the edge)")
    ax.set_title(f"{run.path.name}: {run.status.get('task')} {run.status.get('condition')} seed {run.status.get('seed')}")
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.13),
              ncol=min(len(unique), 8), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def pairs(paths: list[Path]) -> str:
    """Markdown table comparing each run that had interventions with its C1 twin (same task and seed).

    The difference is on the check score of the final pick: test once graded, else probe.
    These are the candidates for the "helped" and "did not help" trajectories.
    """
    runs = [load(p) for p in taxonomy.find_runs(paths)]
    c1 = {(r.status.get("task"), r.status.get("seed")): r for r in runs if r.status.get("condition") == "C1"}
    lines = ["| Run | Condition | Task | Seed | Interventions | Final check | C1 twin final check | Difference | Verdict |",
             "|---|---|---|---|---|---|---|---|---|"]
    found = 0
    for r in runs:
        if r.status.get("condition") == "C1" and not r.applied:
            continue
        twin = c1.get((r.status.get("task"), r.status.get("seed")))
        mine, theirs = _final_check(r), _final_check(twin) if twin else (None, "")
        if twin is None or twin is r or mine[0] is None or theirs[0] is None or mine[1] != theirs[1]:
            continue
        diff = mine[0] - theirs[0]
        helped = better(r.tree, mine[0], theirs[0])
        verdict = "helped" if helped else ("no difference" if diff == 0 else "hurt")
        applied = sum(x["outcome"] == "applied" for x in r.applied)
        lines.append(f"| {r.path.name} | {r.status.get('condition')} | {r.status.get('task')} | {r.status.get('seed')} | "
                     f"{applied} | {fmt(mine[0])} ({mine[1]}) | {fmt(theirs[0])} | {diff:+.4f} | {verdict} |")
        found += 1
    if not found:
        return "No intervened run with a matching C1 twin (same task and seed) was found.\n"
    return "\n".join(lines) + "\n"


def _final_check(run: Run) -> tuple[float | None, str]:
    """The final pick's check score (test, else probe) and which one it is."""
    final = run.tree.nodes.get(run.status.get("final_node") or "")
    return taxonomy.check_score(final) if final else (None, "")


def main() -> None:
    """Write the trajectory of one run, or the intervention pairs table for a set of runs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run", nargs="?", type=Path, help="a run folder")
    parser.add_argument("--out", type=Path, help="default: <run>/trajectory/")
    parser.add_argument("--all", action="store_true", help="list every node, not only the key events")
    parser.add_argument("--no-plot", action="store_true", help="skip the figure (no matplotlib needed)")
    parser.add_argument("--pairs", nargs="+", type=Path, metavar="PATH",
                        help="compare intervened runs under these folders with their C1 twins")
    args = parser.parse_args()

    if args.pairs:
        print(pairs(args.pairs))
        return
    if args.run is None:
        parser.error("give a run folder, or --pairs")
    run = load(args.run)
    evs = events(run, every_node=args.all)
    out = args.out or args.run / "trajectory"
    out.mkdir(parents=True, exist_ok=True)
    (out / "timeline.md").write_text(timeline_md(run, evs))
    if not args.no_plot:
        plot(run, evs, out / "trajectory.png")
    print((out / "timeline.md").read_text())
    print(f"written to {out}")


if __name__ == "__main__":
    main()
