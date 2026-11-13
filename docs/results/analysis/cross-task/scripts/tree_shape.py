"""Tree shape per run: depth, width and how improvements went, for the 63 full-plan runs."""
import json, glob, os, statistics, collections
import pandas as pd
rows = []
for r in sorted(glob.glob("runs/_analysis/full_plan/runs/*")):
    name = os.path.basename(r); cond, task = name.split("_")[0], name.split("_")[1][:7]
    c = sorted(glob.glob(r + "/checkpoints/*/"))[-1]; tr = json.load(open(c + "tree.json")); st = json.load(open(c + "status.json"))
    hib = tr["higher_is_better"]; ns = list(tr["nodes"].values()) if isinstance(tr["nodes"], dict) else tr["nodes"]
    by = {n["id"]: n for n in ns}; kids = collections.defaultdict(list)
    for n in ns: kids[n["parent_id"]].append(n["id"])
    depth = {}
    def d(i):
        """Depth of node i in the tree (root drafts are depth 0)."""
        if i in depth: return depth[i]
        p = by[i]["parent_id"]; depth[i] = 0 if p is None else d(p) + 1; return depth[i]
    for n in ns: d(n["id"])
    imp = [n for n in ns if n["operator"] == "improve"]
    better = lambda a, b: (a > b) if hib else (a < b)
    ok = [n for n in imp if n.get("val_score") is not None and by[n["parent_id"]].get("val_score") is not None]
    gains = sum(better(n["val_score"], by[n["parent_id"]]["val_score"]) for n in ok)
    internal = [i for i in by if len(kids[i]) > 0]
    pick = st["final_node"]
    # lineage of the pick and how many improve parents were distinct
    parents = collections.Counter(n["parent_id"] for n in imp)
    rows.append(dict(task=task, cond=cond, seed=int(name[-1]), nodes=len(ns), max_depth=max(depth.values()),
        mean_depth=statistics.mean(depth.values()), pick_depth=depth[pick], depth_ratio=max(depth.values()) / len(ns),
        branch_nodes=sum(len(kids[i]) >= 2 for i in by), mean_children=statistics.mean(len(kids[i]) for i in internal),
        distinct_improve_parents=len(parents), parent_reuse=len(imp) / max(1, len(parents)),
        improve_win_rate=gains / max(1, len(ok)), test=json.load(open(r + "/grade.json"))["score"]))
d = pd.DataFrame(rows); d.to_csv("runs/_analysis/full_plan/tree_shape.csv", index=False)
print(d.groupby("task")[["nodes", "max_depth", "mean_depth", "pick_depth", "depth_ratio", "mean_children", "parent_reuse", "improve_win_rate"]].median().round(3))
