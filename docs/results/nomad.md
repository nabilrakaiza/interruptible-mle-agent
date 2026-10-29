# Nomad: results of the half plan

Sahi's 13 runs on `nomad2018-predict-transparent-conductors`: seeds 0, 1 and 2 of C1, C4 and C5, and seeds 0 and 1 of A1-off and A4-off. Sahi's own results package, with the grades, interventions and analysis CSVs, is in [`../../results/nomad2018/`](../../results/nomad2018/README.md). This page summarises it in the format of [`spooky.md`](spooky.md) and [`cactus.md`](cactus.md). Every number here comes from that package.

Nomad predicts two properties of candidate transparent conductors (formation energy and bandgap) from tabular crystal data. The metric is the mean root mean squared log error (RMSLE) over the two, so **lower is better**. MLE-bench thresholds: median 0.0699, bronze 0.0658, silver 0.0623, gold 0.0559.

## Setup

- **The same as the other tasks:** DeepSeek V4 Flash 0731 through OpenRouter, Docker sandbox, a nominal 2 hours per run.
- **The machine isn't recorded** in the package.
- **Probe split:** about 216 rows.

## Test scores

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.05991 | 0.06169 | 0.06527 | 0.06229 |
| C2 (oracle, from C1) | 0.05980 | 0.06110 | 0.06386 | 0.06159 |
| C3 (top 3, from C1) | 0.05983 | 0.06110 | 0.06472 | 0.06188 |
| C4 | 0.06128 | 0.06080 | 0.06099 | 0.06102 |
| C5 | 0.06089 | 0.06226 | 0.06123 | 0.06146 |
| A1-off | 0.06131 | 0.06072 | n/a | 0.06102 |
| A4-off | 0.05649 | 0.06165 | n/a | 0.05907 |

- **Every run medalled:** 12 silver and 1 bronze, C1 seed 2. Nomad is the only task where any run medalled.
- **No condition is clearly better than another.** C1 alone ranges over 0.0054 across seeds, more than the largest gap between two conditions' means (0.0032).
- **C2 beats C1 on all three seeds,** by 0.0001 to 0.0014. C3 recovers part of it.

## Interventions

| Runs | Fired | What it did |
|---|---|---|
| C4, seed 0 | **twice, live**: pruned n19, then n44 (30 nodes in all) | the first live C4 prunes in the project; see below |
| C4, seeds 1 and 2 | never | none |
| C5, seed 0 | twice, live: deleted 2 findings | both findings cited a node that crashed |
| C5, seeds 1 and 2 | never | none |

**C4 seed 0** fired at n43 and at n50. Both times the anchor was n18:
- after n43, validation had improved 2.4% while the probe got 2.8% worse, over 6 nodes;
- after n50, validation had improved 3.4% while the probe got 3.3% worse, over 5 nodes.

The probe loss held in 96% of bootstrap resamples both times, above the rule's 95%. With the probe at about 216 rows, nomad's probe is large enough for the rule's statistical check to pass, unlike leaf's (89 rows).

Whether the prunes helped can't be read from these numbers: C4 seed 0 scored 0.06128 against C1 seed 0's 0.05991, but they are different runs. Without the run folders here, the C4 rule can't be replayed over the C1 runs.

## Validation against test

Mean gap between the submitted node's validation and test scores (from `analysis/val_test_gap/`):

| C1 | C4 | C5 | A1-off | A4-off |
|---|---|---|---|---|
| −0.0001 | +0.0002 | +0.0002 | **+0.0047** | +0.0015 |

A1-off has the largest gap, as on spooky: without A1, validation is optimistic. The gap is small next to spooky's 0.13, but it's about the size of the difference between a silver and a bronze medal.

## Points to check with Sahi

- **Two C1 runs barely searched:** seed 1 made 17 nodes in 2.76 hours, and seed 2 made 14 nodes in 3.72 hours, against 63 to 82 nodes for the C4 runs. C1 is the baseline, so this weakens every comparison with it. The package says some runs exceeded the 2-hour budget but not why.
- **Mixed providers:** six runs, including all three C1 runs, were served partly or fully by providers other than Baidu (CoreWeave, DeepInfra, BaseTen). All are fp8 by configuration, but C1 seeds 1 and 2 are exactly the slow runs.
- **The machine and Docker setup** aren't recorded.
- **There's no C6 session** for nomad yet.
