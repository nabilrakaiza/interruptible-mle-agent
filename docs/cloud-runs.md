# Running on Colab or Kaggle

Extra machines for the run backlog. Written by role 2; role 1 owns the run schedule and can adopt or replace this.

Both platforms work the same way:
1. A notebook clones the repo with a read-only token and installs it.
2. It reads API keys from the platform's secrets.
3. It calls `scripts/cloud_run.py`, which starts the run or resumes it if it was cut off.

One command, run again after any interruption, always continues the same run.

## What runs where

| | Colab (free) | Kaggle | Laptop |
|---|---|---|---|
| Notebook | `notebooks/colab_run.ipynb` | `notebooks/kaggle_run.ipynb` | `python scripts/cloud_run.py ...` |
| Runs with the browser closed | no (Pro+ only) | yes, *Save & Run All* | yes |
| Session limit | about 12 h; about 90 min idle disconnect | about 12 h | none |
| Where the run lives | local disk, copied to Drive every 2 min | `/kaggle/working`, kept as output | `runs/` |
| After an interruption | run all cells again | new version with the old output attached and `RESTORE_FROM` set | rerun the command |
| CPU | about 2 cores | about 4 cores | varies |
| Docker | no | no | yes, once role 1's image exists |

## One-time setup

1. **GitHub token.** The repo is private.
   - Create a fine-grained token with *Contents: read-only* on `nabilrakaiza/interruptible-mle-agent`.
   - Store it as the secret `GITHUB_TOKEN`.
   - The notebook removes it from `.git/config` after cloning and masks it in errors.
2. **API keys** as secrets: `OPENROUTER_API_KEY` (experiments) and/or `GEMINI_API_KEY` (testing).
   - **Colab:** the key icon in the left bar, with notebook access switched on.
   - **Kaggle:** *Add-ons → Secrets*. Kaggle also needs Internet switched on in *Settings*, which requires a phone-verified account.
3. **Data (real tasks only).**
   - Prepare each competition once with `mlebench prepare -c <task>`, using an account that accepted its rules.
   - Share that one copy: a Drive folder for Colab, or a private Kaggle Dataset attached to the notebook.
   - Every run then sees identical splits.
   - How the evaluator is pointed at the data is up to role 3's `evaluation.prepare`.

## Using a notebook

**Colab** (`notebooks/colab_run.ipynb`):
1. Edit only the **Settings** cell: condition file, task, seed, provider, `BRANCH`, `SMOKE`.
2. `SMOKE = True` runs the toy task instead of a real one, as a quick check. `DRY_RUN = True` needs no API key at all.
3. *Run all*, and keep the tab active. After a disconnect, reconnect and *Run all* again.

**Kaggle** (`notebooks/kaggle_run.ipynb`): see the full plan below.

The last cell writes the trajectory figure and timeline into each run folder (`scripts/trajectory.py`).

## The full plan on Kaggle (insults and pizza)

From 1 Nov 2026, the two tasks nobody covers run the full plan on Kaggle CPU: 21 runs of 4 hours each per task, 42 runs in all, listed in `configs/kaggle_sessions.yaml`.
- **Two runs per session.** A Kaggle session ends at 12 hours, and three 4-hour runs plus setup would not fit. Each session runs one condition and seed on both tasks, about 8.5 hours.
- **Five notebooks, `imle-slot-1` to `imle-slot-5`,** each a copy of `notebooks/kaggle_run.ipynb`. A Kaggle account can run about five batch CPU sessions at once, and only a notebook's latest version can be downloaded, so each slot runs one session per round. Session `s` runs in slot `(s - 1) % 5 + 1`.
- **Rounds:** 1 is sessions 1–5 (seed 0 of every condition), 2 is 6–10 (seed 1), 3 is 11–15 (seed 2), 4 is 16–20 (seeds 3 and 4 of C1, C4 and C5), and 5 is session 21. A round takes about 8.5 hours.
- **CPU only.** GPU sessions have a 30-hour weekly quota, and the scripts don't use a GPU.

**Data.** The private Kaggle dataset `imle-kaggle-data` holds `<task>/prepared/public` and `<task>/prepared/private` for both tasks. The evaluator needs the private answers while the run goes, for each node's test score (analysis only). The run folder holds them anyway, in `stand_in/harness/labels.csv`. The notebook finds both folders wherever Kaggle mounts them.

**Packages.** The notebook builds a Python 3.13.6 environment with the sandbox image's versions (`Dockerfile`, `docker-requirements.txt`), so the agent's scripts see the versions its prompt lists, as on the Mac. Scripts are limited to 2 threads, like the Docker sandbox.

**Each round:**
1. In each slot notebook, set `SESSION` and click *Save Version → Save & Run All (Commit)*.
2. When the round is done, on the Mac:
   ```bash
   KAGGLE_BIN=~/Documents/GitHub/mle-bench/.venv/bin/kaggle \
   MLEBENCH_PYTHON=~/Documents/GitHub/mle-bench/.venv/bin/python \
       python scripts/kaggle_collect.py --round 1
   ```
   This downloads each slot's latest output into `runs/kaggle/`, checks it is the expected session, reports which runs finished, and grades them.
3. Start the next round only after collecting, since a new version replaces the slot's output.

**A cut-off session:** attach the slot notebook's own output as an input and run the same `SESSION` again; each run continues from its last checkpoint.

**First time:** `TEST = True` runs both tasks for 15 minutes as `test_...` runs. Collect them with `--test`.

**Differences from the Mac runs, for the report:** no Docker (scripts can reach the network and files outside their folder, so A1's screen is the only leakage protection); about 4 cores and 30 GB RAM instead of 2 CPUs and 4 GB, though scripts are capped at 2 threads; the C6 sessions for these tasks still run on the Mac, with the dashboard.

## The launcher on its own

```bash
python scripts/cloud_run.py --config configs/conditions/c1_autonomous.yaml \
    --task spooky-author-identification --seed 0 --provider openrouter \
    --runs-root /content/runs --sync-to /content/drive/MyDrive/imle/runs
```

- **Run folder name:** fixed as `<condition>_<task>_seed<seed>`, so every call finds the same run.
- **Start, resume or skip:**
  - no complete checkpoint: start;
  - unfinished: `--resume`;
  - finished: nothing to do, unless `--budget-hours` asks for more time than the run had (below).
- **Budget and extending (22 Oct):** `--budget-hours H` sets a new run's total budget instead of `budget.wall_clock_s`. Given again for a finished run with less, it continues that run from its last checkpoint until the run has H hours in total, and picks the final node again. It never extends twice, so a retried command is safe. Extend both runs of a C1/C4 pair, never one alone, and keep the monitor running during the extension.
- **Restore on a fresh machine:** if the local folder has no checkpoint, it is copied back from `--sync-to` or `--restore-from` first.
- **Syncing:** while the run goes, the folder is copied to `--sync-to` every `--sync-every` seconds (default 120), only files that changed. A checkpoint copied half-written is harmless, because resume skips incomplete checkpoints.
- **Retries:** if the run exits with an error, such as a long LLM outage, it waits `--retry-wait` seconds (default 600) and resumes, up to `--retries` times (default 2).
- **Toy task:** `--smoke [--dry-run] --nodes N` uses the toy task instead of a real one.

## Things that affect the experiments

- **No sandbox isolation.** Neither platform can run Docker, so scripts run with `--sandbox subprocess`:
  - they have network access;
  - they could read files outside their folder, including the evaluator's labels.

  The leakage protection then rests on A1's screen alone. State this in the report, and do not mix sandbox types within one comparison.
- **Hardware changes results.** A 4-hour budget buys less search on a slower machine.
  - Run every condition of a given task and seed on the same kind of machine. For example, do not split C1 and C4 of `spooky` seed 0 across Colab and a laptop.
  - Each start and resume appends the machine to `machine.jsonl` in the run folder (platform, CPUs, memory, Python), so this can be checked afterwards.
- **Resumes on another machine.** A Colab run that resumes after a disconnect may land on a different VM. `machine.jsonl` records each one.
