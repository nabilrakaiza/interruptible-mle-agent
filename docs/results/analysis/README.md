# Full-plan analysis: spooky, insults and pizza

Nabil's analysis of the 63 full-plan runs (21 per task), exported on 9 Nov 2026 from the live doc [Full-plan results](https://claude.ai/artifact/1AHcCcSLLuLfqSGPkTFe5W#aee780ae-bfc4). The doc stays the editable version; these files are a snapshot of it.

**Tabs, in reading order** (the per-task tabs sit in each task's folder):
- [`cross-task-summary.md`](cross-task-summary.md): what holds on all three tasks, what differs and why.
- [`../spooky/analysis.md`](../spooky/analysis.md), [`../insults/analysis.md`](../insults/analysis.md), [`../pizza/analysis.md`](../pizza/analysis.md): every run, charts, final models, and a report draft per task.
- [`reliability-checks.md`](reliability-checks.md): A1's leakage stress test and the prompt-injection check.
- [`tree-shape.md`](tree-shape.md): why some runs go deep and others wide.
- [`further-analyses.md`](further-analyses.md): other final-pick rules, when runs found their pick, optimism over a run, and a Friedman test across tasks.

**Files:**
- `../<task>/analysis/charts/`: images of the doc's charts and two annotated trajectories per task.
- `../<task>/analysis/tables/runs.csv`: one row per run. `../insults/analysis/` also has the complex-model check (`tables/insults_complex.csv`, `scripts/`).
- `cross-task/tables/`: outcomes, cost, validation–test gap, probe fidelity, error taxonomy, C4 replay, finding accuracy, tree shape, the further analyses, the reliability checks and the MLE-bench comparison, with `SUMMARY.md` (the first pass over all of them).
- `cross-task/scripts/`: the scripts written for this analysis. They read the run folders on Nabil's Mac (`runs/grid/`, `runs/kaggle/`, `runs/_analysis/`), which are not in git; the project's own scripts (`scripts/outcomes.py`, `scripts/replay_policy.py` and the others) made the remaining tables.

The leaf, cactus and nomad tasks and the two runs with an LLM as the monitor are not part of this analysis; they are summarised in [`../full-plan.md`](../full-plan.md) and in their task folders.
