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

1. Open the notebook and edit only the **Settings** cell:
   - condition file, task, seed, provider;
   - `BRANCH`: use `nabil-coreagent` until PR #2 is merged;
   - `SMOKE`.
2. Keep `SMOKE = True` (the toy task) until role 3's evaluator exists. `DRY_RUN = True` needs no API key at all.
3. **Colab:** *Run all*, and keep the tab active. After a disconnect, reconnect and *Run all* again.
4. **Kaggle:** *Save Version → Save & Run All*. If a run was cut off:
   - start a new version;
   - attach the old version's output as an input;
   - set `RESTORE_FROM` to its `runs` folder.

The last cell writes the trajectory figure and timeline into each run folder (`scripts/trajectory.py`).

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
