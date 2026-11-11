# C6 seed 102: intervention notes

**Intervener: Claude (Opus 5.5), not a human.** The user could not watch this run, so Claude made the
live decisions, checking about every 15 min. The criteria were the same as seed 101: prune non-CNN
approaches, regressions, and buggy or weak branches, and focus on the best branches. This is a
limitation for C6 and must be stated in the write-up.

Run: 4 h budget, started 11:26 11 Nov 2026 (+08), A1 evaluator, MacBook Pro M-series, training on
CPU in Docker/Colima (2 CPU, 5 GB).

## Check log
| time (+08) | state | action |
|---|---|---|
| 11:39 | 0 scored nodes; 1st coding call (n0) in flight ~13 min, HTTPS open to OpenRouter (seed 101's 1st coding call took 552 s) | none |
| 11:54 | n0 CNN 0.99881; n1 PCA+MLP 0.95715; n2 handcrafted+HGB 0.99376; n3 drafting | **prune n1, n2**: not CNN models (seed-101 rule); n1 also weakest |
| 12:09 | n1, n2 prune applied. n0 CNN 0.99881 -> n7 (+flips) 0.99905 (best) -> n8 (+TTA) 0.99878; n3 logreg 0.94621, n4 ExtraTrees 0.97912, n5 buggy (n3 branch), n6 sklearn MLP 0.96483 | **prune n3, n4, n6**: not CNN models. n5 already buggy, under n3. n8 kept: TTA dip of 0.0003 is within noise |
| 12:12 | n3, n4 applied; n6 dropped as 'already pruned' (pruning n3 cascades to its subtree n5, n6). New best n9 (child of n7) 0.99934 | none |
| 12:24 | NOTE: Mac on battery (59%, discharging); user alerted. New draft n10 strided CNN 0.99995 (best); n13 (n10 + translation) 0.99972; n11 (n10 + EMA) 0.75277, n12 (EMA decay fix) 0.75277, unchanged; n9 0.99934 | **prune n11** (cascades to n12): broken EMA branch, fix failed. **prune n8**: regression vs parent n7, dominated |
| 12:39 | n11, n8 applied. Still ON BATTERY 58%. New non-CNN draft n14 (PCA + logreg/ExtraTrees/MLP voting) 0.96419 -> n15 (+HGB) 0.96802 -> n16 (HGB tuned) 0.96815. Best still n10 0.99995 | **prune n14** (cascades to n15, n16): not a CNN model, 3 steps spent on it |
| 12:54 | n14 applied (n15, n16 cascaded). n17 (child of n16, in flight when pruned; ensemble + small CNN) 0.98971, arrived already pruned. Still on battery 55%. Live: n10 0.99995 (best), n13 0.99972, n9 0.99934 | none |
| 13:09 | No new scored node in 15 min: n18 (residual CNN, 25 epochs, early stopping) training in Docker for 15 min (timeout 20 min). Disk 2.3 GB (was 3.3), swap 1.9 GB; battery 51% discharging | none |
| 13:24 | Mac display slept briefly around 13:10 (user), no system-sleep event in the log, run unaffected. n18 residual CNN (flips + rot90) 0.99997 = new best; n19 in flight. Disk 2.5 GB, battery 47% discharging | **prune n0** (cascades to n7, n9): weakest CNN line (0.99934), well below n18/n10; focus on the best branches |
| 13:39 | n0 applied (n7, n9 cascaded). n19 (n18 + squeeze-excitation) 0.99998 = new best. Battery 44% discharging, disk 2.5 GB | **prune n13**: regression vs parent n10 (same rule as n8) |
| 13:54 | n13 applied. n20 (n18 + snapshot ensemble) 0.99997, ties parent. Live: n19 0.99998 (best), n18/n20 0.99997, n10 0.99995. Battery 40% discharging | none: no regressions or non-CNN nodes |
| 14:09 | Mac back on AC (38%, charging). n21 (n19 + mixup) 0.99995, 0.00003 below parent n19 0.99998, within noise; equals n10. Best n19 0.99998. Disk 2.5 GB, swap 2.0 GB | none: n21 dip too small to count as a regression (n8/n13 dropped 0.0002-0.0003) |
| 14:24 | New draft n22 depthwise-separable CNN 0.999981 = new best (just above n19 0.999979). All live nodes CNN, all >= 0.99995. AC charging 39%, disk 2.4 GB, swap 2.3 GB | none |
| 14:39 | n23 (n22 + cutout) 0.99992, 0.00006 below parent n22 0.99998, within noise. Best n22 0.999981. AC, disk 2.4 GB, swap 2.6 GB | none: rule used = prune only regressions >= ~0.0001 (n8, n13 were 0.0002-0.0003) |
| 14:54 | n24 (n22 + photometric aug) 0.99997, 0.00001 below parent, noise. Best n22 0.999981. AC, disk 2.4 GB | none |
| 15:09 | n25 (n22 + concat GAP/GMP features) 0.99992, 0.00006 below parent, noise. Best n22 0.999981. Disk 1.5 GB (swap grew to 2.8 GB), still above the 500 MB floor | none |
| 15:24 | n26 new draft VGG-style CNN 0.99992. Best n22 0.999981. ~6 min of budget left; disk 1.6 GB | none: last check before the budget ends |
| 15:39 | RUN DONE 15:26 (stop_reason budget, 35 steps, 27 nodes, 32 LLM calls, about $0.10). Final node n22 (best_val 0.999981), submitted. Not graded yet | none; check-ins stopped |

## Summary of Claude's interventions (all applied unless noted)
- 11:54 prune n1, n2: not CNN models
- 12:09 prune n3 (n5, n6 cascaded), n4: not CNN models (n6 prune dropped as already pruned)
- 12:24 prune n11 (n12 cascaded): broken EMA, val 0.75; prune n8: TTA regression
- 12:39 prune n14 (n15, n16, n17 cascaded): non-CNN sklearn ensemble
- 13:24 prune n0 (n7, n9 cascaded): weakest CNN line, focus on n10/n18
- 13:39 prune n13: regression vs parent n10
- Rule: prune non-CNN models, broken branches, and regressions of >= ~0.0001 vs the parent; keep dips within noise (n21, n23, n24, n25)

## Debrief
None. The user asked for the report straight after the run (17:00 11 Nov), so there was no human review or debrief before grading. Graded afterwards: test 0.99995 (n22).
