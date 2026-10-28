# Cactus: the half plan, all seeds

26 to 28 Oct 2026, Dziand's Mac (Apple M2, 8 GB). Every half-plan run on `aerial-cactus-identification`: C1, C4 and C5 with seeds 0 to 2, and A1-off and A4-off with seeds 0 and 1. Thirteen runs; C2 and C3 come from the C1 trees.

Cactus is ROC AUC, so **higher is better**. MLE-bench thresholds: median 0.9991, and bronze, silver and gold are all 1.0, so no medal is reachable short of a perfect score.

## Setup

- **Command:** `scripts/cloud_run.py --config configs/conditions/<condition>.yaml --task aerial-cactus-identification --seed <s> --budget-hours 2 --sandbox docker --runs-root runs/grid --evaluator a1 --retries 0`, one run at a time, under `caffeinate`.
- **Model:** DeepSeek V4 Flash 0731 through OpenRouter, fp8 (the `base.yaml` default).
- **Evaluator:** A1, Docker sandbox (Colima, 2 CPUs and 5 GB), 2 hours per run. Code: `main` at 92cff79, so PR #7 is in every run.
- **Data:** prepared from the Kaggle zip with MLE-bench's own prepare function; the public and private checksums match MLE-bench's.
- **Gate:** a paid 20-minute, 3-node smoke run of C1 first ($0.018); it passed before any grid run started.
- **Times (SGT):** C1, C4 and C5 seed 0, then C1 and C4 seed 1, on the night of 26 to 27 Oct; the rest of seeds 1 and 2 on 27 Oct, 12:43 to 22:10; the ablations 23:02 to 07:04.
- **Health:** 0 failed LLM calls in any run, and no run was restarted. The grid stopped once, at 14:44 on 27 Oct, between runs: macOS swap had left under 500 MB of disk. It resumed at 16:06 after space was freed; no run was cut short.
- **Cost:** $1.14 in all, including the smoke run.

## Results

| Run | Nodes (working) | Timeouts | LLM calls | Cost | **Score** |
|---|---|---|---|---|---|
| C1 seed 0 | 35 (32) | 2 | 40 | $0.061 | **0.99977** |
| C1 seed 1 | 18 (17) | 1 | 21 | $0.030 | **0.99994** |
| C1 seed 2 | 26 (21) | 2 | 32 | $0.129 | **0.99917** |
| C4 seed 0 | 39 (37) | 1 | 44 | $0.063 | **0.99936** |
| C4 seed 1 | 22 (17) | 1 | 26 | $0.095 | **0.99992** |
| C4 seed 2 | 50 (47) | 1 | 60 | $0.232 | **0.99979** |
| C5 seed 0 | 27 (24) | 1 | 31 | $0.052 | **0.99999** |
| C5 seed 1 | 44 (40) | 1 | 50 | $0.158 | **0.99927** |
| C5 seed 2 | 45 (41) | 2 | 52 | $0.118 | **0.99984** |
| A1-off seed 0 | 22 (20) | 1 | 25 | $0.045 | **0.99972** |
| A1-off seed 1 | 26 (23) | 2 | 30 | $0.054 | **0.99993** |
| A4-off seed 0 | 26 (24) | 1 | 27 | $0.028 | **0.99961** |
| A4-off seed 1 | 36 (33) | 1 | 37 | $0.060 | **0.99940** |

All thirteen are valid and above the median. None medalled.

### By condition

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.99977 | 0.99994 | 0.99917 | 0.99963 |
| C2 (oracle, from C1) | 0.99982 | 0.99994 | 0.99942 | 0.99973 |
| C3 (top 3, from C1) | 0.99977 | 0.99994 | 0.99929 | 0.99967 |
| C4 | 0.99936 | 0.99992 | 0.99979 | 0.99969 |
| C5 | 0.99999 | 0.99927 | 0.99984 | 0.99970 |
| A1-off | 0.99972 | 0.99993 | | 0.99982 |
| A4-off | 0.99961 | 0.99940 | | 0.99950 |

The spread between seeds of one condition (up to 0.0008) is larger than any gap between condition means (at most 0.0003). On cactus the conditions cannot be told apart.

## Findings

### 1. No interventions fired, so C4 and C5 were C1

Every C4 and C5 trajectory reports 0 interventions applied and 0 dropped, and no run wrote a queue. The divergence and finding monitors never triggered on this task, so C4 and C5 ran the same search as C1, and their differences from it are seed noise.

### 2. Final-node selection costs almost nothing

C2 beats C1 by 0.0001 on average; C3 recovers about 40% of that. The largest loss is C1 seed 2 (0.99917 submitted, 0.99942 available). Across all thirteen runs the selection regret on test is at most 0.0003 (C4 seed 0).

### 3. Without A1, the agent did not fool itself here

On spooky, A1-off seed 1 fitted a stacker on its own validation split and drifted 0.13 from test. Cactus shows nothing like it. Validation minus test, over every working node:

| Run | Mean gap | Largest gap |
|---|---|---|
| A1-off seed 0 | +0.0010 | +0.0059 (n3) |
| A1-off seed 1 | +0.0005 | +0.0041 (n3) |
| A4-off seed 0 | +0.0009 | +0.0058 (n2) |
| A4-off seed 1 | +0.0028 | +0.0077 (n2) |
| C1, C4, C5 (9 runs) | -0.0003 to +0.0008 | +0.0027 to +0.0085 |

The largest gaps sit on early, weak nodes in every condition, with A1 or without it. With every model near 0.999 AUC, there is little room for an own-split leak to show.

## Files

- `cactus/grades/`: MLE-bench's `grade.json` for each run.
- `cactus/outcomes/`: `scripts/outcomes.py runs/grid`.
- `cactus/trajectories/`: `scripts/trajectory.py` for each run, timeline and plot.
