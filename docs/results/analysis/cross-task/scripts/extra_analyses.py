"""Four extra analyses on the 63 full-plan runs: selection rules, time to the pick, optimism over time, Friedman test."""
import json, glob, os, statistics, collections
from datetime import datetime
import numpy as np, pandas as pd
from scipy.stats import friedmanchisquare, spearmanr
ROWS = {"spooky": (3524, 1762), "detecti": (789, 395), "random-": (576, 288)}
out = collections.defaultdict(list)
for r in sorted(glob.glob("runs/_analysis/full_plan/runs/*")):
    name = os.path.basename(r); cond = name.split("_")[0]; task = name.split("_")[1][:7]; seed = int(name[-1])
    c = sorted(glob.glob(r + "/checkpoints/*/"))[-1]; tr = json.load(open(c + "tree.json")); st = json.load(open(c + "status.json"))
    hib = tr["higher_is_better"]; s = 1 if hib else -1
    ns = sorted([n for n in (tr["nodes"].values() if isinstance(tr["nodes"], dict) else tr["nodes"])], key=lambda n: int(n["id"][1:]))
    w = [n for n in ns if n["status"] == "working" and None not in (n.get("val_score"), n.get("probe_score"), n.get("test_score"))]
    nv, npb = ROWS["spooky" if task.startswith("spooky") else task]
    best = lambda key: max(w, key=lambda n: s * key(n))
    oracle = best(lambda n: n["test_score"])["test_score"]
    rules = {"validation (actual rule)": lambda n: n["val_score"], "probe": lambda n: n["probe_score"],
             "validation + probe (row-weighted)": lambda n: (nv * n["val_score"] + npb * n["probe_score"]) / (nv + npb)}
    # mean rank of validation and probe
    vr = pd.Series({n["id"]: s * n["val_score"] for n in w}).rank(); pr = pd.Series({n["id"]: s * n["probe_score"] for n in w}).rank()
    rules["mean rank of validation and probe"] = lambda n: s * (vr[n["id"]] + pr[n["id"]])
    for k, f in rules.items():
        p = best(f); out["sel"].append(dict(task=task, cond=cond, seed=seed, rule=k, test=p["test_score"], loss=s * (oracle - p["test_score"])))
    # 2. time to the final pick
    t0 = datetime.fromisoformat(ns[0]["started_at"]); tend = datetime.fromisoformat(max(n["finished_at"] for n in ns if n.get("finished_at")))
    pick = next(n for n in ns if n["id"] == st["final_node"]); tp = datetime.fromisoformat(pick["finished_at"])
    out["time"].append(dict(task=task, cond=cond, seed=seed, pick_frac_time=(tp - t0) / (tend - t0), pick_frac_nodes=(ns.index(pick) + 1) / len(ns)))
    # 3. optimism and selection loss over the run: current best-validation node at 25/50/75/100% of nodes
    for q in (0.25, 0.5, 0.75, 1.0):
        upto = ns[: max(1, int(round(q * len(ns))))]; ww = [n for n in upto if n in w]
        if not ww: continue
        cur = max(ww, key=lambda n: s * n["val_score"]); orc = max(s * n["test_score"] for n in ww)
        out["gap"].append(dict(task=task, cond=cond, seed=seed, q=q, gap=s * (cur["test_score"] - cur["val_score"]), loss=orc - s * cur["test_score"], test=cur["test_score"]))
    out["final"].append(dict(task=task, cond=cond, seed=seed, test=json.load(open(r + "/grade.json"))["score"], hib=hib))
sel = pd.DataFrame(out["sel"]); tim = pd.DataFrame(out["time"]); gap = pd.DataFrame(out["gap"]); fin = pd.DataFrame(out["final"])
for k, v in (("sel", sel), ("time", tim), ("gap", gap)): v.to_csv(f"runs/_analysis/full_plan/extra_{k}.csv", index=False)
A1 = lambda d: d[d.cond != "A1-off"]
print("== 1. selection rules (A1-on runs): mean test and mean loss to the best node")
print(A1(sel).groupby(["task", "rule"])[["test", "loss"]].mean().round(4).to_string())
wins = A1(sel).pivot_table(index=["task", "cond", "seed"], columns="rule", values="test")
for t, g in wins.groupby(level=0):
    s = -1 if t.startswith("spooky") else 1
    for r in ["probe", "validation + probe (row-weighted)", "mean rank of validation and probe"]:
        d = s * (g[r] - g["validation (actual rule)"]); print(f"  {t} {r}: better on {(d > 1e-9).sum()}, worse on {(d < -1e-9).sum()}, same {(d.abs() <= 1e-9).sum()} of {len(d)}")
print("== 2. time to the final pick (share of the run's span)")
print(tim.groupby("task")[["pick_frac_time", "pick_frac_nodes"]].describe(percentiles=[.25, .5, .75]).round(2).to_string())
print("== 3. optimism (test - val, oriented) and selection loss of the current best-validation node, A1-on, median")
print(A1(gap).groupby(["task", "q"])[["gap", "loss"]].median().round(4).unstack(0).to_string())
print("== 4. Friedman")
fin["good"] = np.where(fin.hib, fin.test, -fin.test)
m = fin[fin.cond.isin(["C1", "C4", "C5"])].pivot_table(index=["task", "seed"], columns="cond", values="good")
print("C1/C4/C5, 15 blocks:", friedmanchisquare(m.C1, m.C4, m.C5), "mean ranks (1 = best):", (-m).rank(axis=1).mean().round(2).to_dict())
m5 = fin[fin.seed <= 2].pivot_table(index=["task", "seed"], columns="cond", values="good")
print("all 5 conditions, seeds 0-2, 9 blocks:", friedmanchisquare(*[m5[c] for c in m5.columns]), "mean ranks:", (-m5).rank(axis=1).mean().round(2).to_dict())
