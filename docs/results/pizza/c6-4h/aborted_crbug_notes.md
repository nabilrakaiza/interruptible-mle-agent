# C6 notes: random-acts-of-pizza seed 100 (4 h)

All monitoring and interventions in this run are by Claude (Claude Code), not a human.

## 12:28 check (Claude)
- Power: battery 95%, discharging. Swap 2.2 GB, disk 1.7 GB free. Controller alive, no Traceback.
- n0 (TF-IDF + LR) and n1 (GBM) are both buggy with `invalid_submission: ids do not match predict.csv: 2027 rows, expected 2026`.
- Cause (harness, not the agents): workspace/input/predict.csv has 2 bare `\r` characters inside unquoted text fields. pandas 3.1.0 (this Mac's .venv) `to_csv` does not quote a bare `\r`, so `read_csv` splits one test post into two rows. That gives 2027 rows against 2026 labels. The bad post is in MLE-bench's fixed test set, so seeds 0-2 and 100-105 are all affected. Nabil's Kaggle runs probably had a different pandas version.
- No prune. Every node will fail the same way, so I asked the user what to do.

## 12:4x (Claude), run stopped on the user's choice ("stop, pin pandas, rerun")
- Stopped the run at about 12:40; moved here (runs/aborted/C6_random-acts-of-pizza_seed100_crbug).
- Pinning pandas does NOT fix it: pandas 2.2.3 also leaves a bare `\r` unquoted. I restored pandas 3.1.0; the env is unchanged.
- Root cause: 1 record in MLE-bench's public test.json (and 4 in train.json) has a bare `\r` in request_text_edit_aware. Every pizza test row goes into predict.csv, so this hits every seed and every machine that uses this data. It's unclear why Nabil's Kaggle runs were not affected. Maybe Kaggle's copy of the data has its line endings normalized (not verified).
