"""Per-experiment results on our six tasks, from MLE-bench's official grading reports."""
import csv, glob, json, os, statistics, sys
T = {"spooky-author-identification": "spooky", "detecting-insults-in-social-commentary": "insults",
     "random-acts-of-pizza": "pizza", "aerial-cactus-identification": "cactus",
     "nomad2018-predict-transparent-conductors": "nomad", "leaf-classification": "leaf"}
d = os.environ["MLEB"]
exp = {}
for f in glob.glob(d + "/rge_*.csv"):
    for row in csv.reader(open(f)):
        if len(row) == 2 and row[0] != "experiment_id":
            exp.setdefault(row[0].strip(), set()).add(row[1].strip())
out = []
for e, groups in sorted(exp.items()):
    recs = {k: [] for k in T}
    for g in groups:
        for f in glob.glob(f"runs/{g}/*.json"):
            for r in json.load(open(f))["competition_reports"]:
                if r["competition_id"] in T:
                    recs[r["competition_id"]].append(r)
    for c, rs in recs.items():
        if not rs:
            continue
        sc = [r["score"] for r in rs if r.get("score") is not None]
        out.append({"experiment": e, "task": T[c], "seeds": len(rs), "valid": sum(bool(r.get("valid_submission")) for r in rs),
                    "mean": round(statistics.mean(sc), 4) if sc else None, "best": (min(sc) if rs[0]["is_lower_better"] else max(sc)) if sc else None,
                    "medals": sum(bool(r.get("any_medal")) for r in rs), "gold": sum(bool(r.get("gold_medal")) for r in rs),
                    "above_median": sum(bool(r.get("above_median")) for r in rs)})
json.dump(out, open(d + "/per_task.json", "w"), indent=0)
print(len(exp), "experiments;", len(out), "rows")
