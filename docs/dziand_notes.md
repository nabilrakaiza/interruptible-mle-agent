# Role 3 notes: A1 evaluation, A4 reflection, C5

Written 24 Oct 2026 by role 3 (Dziand). How A1, A4 and the C5 policy plug into the controller, and the decisions behind them.

## The calls the controller makes

Role 3's code implements the signatures in `docs/core-agent-assumptions.md` exactly, so the controller needs no change and no branching of its own. `--evaluator a1` (the default) now works.

| When | Call | Module |
|---|---|---|
| Once, at the start of a run | `evaluation.prepare(task, run_dir, seed) -> ctx` | `imle/agents/evaluation.py` |
| Before each script runs, if `agents.evaluation` | `evaluation.screen(llm, script) -> str \| None` | same |
| After each script runs | `evaluation.score(node_dir) -> result` (val_score, probe_score, test_score, error) | same |
| After each node, if `agents.reflection` | `reflection.reflect(llm, tree, findings, run_dir) -> list[dict]` | `imle/agents/reflection.py` |
| At each safe point, if the condition lists it | `finding_correction.decide(run_dir, ck) -> list[dict]` | `imle/policies/finding_correction.py` |

The A1-off and A4-off switches are selected from `cfg["agents"]` as follows:

- **A1-off** (`agents.evaluation: false`):
  - `prepare` picks the self-report scoring strategy (`evaluation.SelfReportScoring`) and freezes that choice with the harness, so `score` and a resumed run use it without re-reading the config.
  - The controller already skips `screen` in this case.
- **A4-off** (`agents.reflection: false`): the controller already never calls `reflect` and passes no findings to A3's prompt. `reflect` itself needs no switch.

## Files written under the run folder

```
runs/<run_id>/
  stand_in/input/        what the agent sees (the stand-in's data layer)
  stand_in/harness/      labels and meta, read-only after freezing
  a1/harness.json        frozen spec: task, mode, metric, split sizes, SHA-256 of each harness file
  a1/harness.sha256      hash of harness.json
  a1/context.json        the task context returned by prepare
  a4/state.json          {"next_boundary": <finished nodes>, "written": {finding id: text}}
  a4/errors.jsonl        A4 replies that stayed invalid after the retries
```

## LLM calls

Every LLM call goes through the injected `llm(agent=..., system=..., user=...)`, which is `imle.llm.OpenAICompatibleLLM` in real runs. It logs each call to `llm_calls.jsonl`, through role 1's `log_llm_call` once that is merged, so role 3's code needs no separate adapter. The agent names logged are `reflection` (A4) and `evaluation` (A1's optional LLM review, used only by the stress test).

Structured output (`reflection.ask_json`):

- The reply must be JSON, which is validated with pydantic and with extra checks such as node IDs that exist.
- An invalid reply is retried with the error shown, up to `max_retries` times (default 2).
- After the last retry, `StructuredOutputError` is raised.
- `LLMUnavailable` is never caught, so the controller's outage handling still applies.

## Decisions

- **Data layer, splits and metrics are the stand-in's.** This makes A1, A1-off and A4-off runs score exactly the rows the C1 runs did: val 0.2, probe 0.1, stratified, `splits.seed` 0, and MLE-bench's metric code. `imle/splits.py` and `imle/metrics.py` are independent numpy versions, used for synthetic data and as a cross-check (`tests/test_shared_pieces.py` checks that the log loss equals the stand-in's).
- **Harness: deterministic, frozen, not LLM-written.**
  - On disk it is the stand-in's labels plus a spec with the SHA-256 of every file. The files are read-only after freezing.
  - `score` verifies the hashes before every scoring; a changed harness gives `harness_integrity: ...` and an invalid node.
  - `prepare` never rebuilds a frozen harness. A repeated call verifies it and returns the saved context, which makes a crash inside `prepare` recoverable.
- **Prediction format.**
  - The script writes `OUTPUT_DIR/predictions.csv` for every row of `predict.csv`. Validation, probe and test rows are mixed and unlabelled, so A3 never sees probe labels and cannot tell probe rows from validation rows.
  - All scoring happens outside the script.
  - With A1 off, the validation rows are moved into `train.csv` with their labels. The script makes its own split and writes `OUTPUT_DIR/val_score.json` as `{"val_score": x}`. Probe and test are still scored by the harness.
- **Probe carve-out.** Every condition, including A1-off, uses the same probe rows (`tests/test_switches.py::test_a1_off_split_is_the_a1_on_split`).
- **Leakage screen.**
  - The rules are AST-based and fire only on patterns they can prove, because false positives reject working nodes and inflate the reported false-positive rate. They are:
    - **R0, harness access (leak):** paths naming the harness, `labels.csv`, MLE-bench, a private folder, or a parent folder.
    - **R1, target as feature (leak).**
    - **R2, statistics from `predict.csv` (warn only):** MLE-bench allows unsupervised use of the test inputs, so it does not reject the script.
    - **R3, validation rows used to fit the model that is then evaluated on them (leak).**
  - The live `screen` uses the rules only, so it is deterministic and costs nothing. The LLM review is opt-in, through `screen_script(..., llm=...)` and the stress test's `--llm-review`.
  - Under this prediction format, R1 and R3 can only inflate a script's own printed numbers, not the harness's validation score. Through the harness, a script can only leak by reading the labels (R0), which only the subprocess sandbox allows. With A1 off, R1 and R3 do inflate the self-reported score that selection uses, and no screen runs: that is part of what the ablation measures.
- **Finding schema** (`imle/findings.py`): `{id, text, step, effect, evidence: [{node_id, val_score, probe_score}]}`.
  - The ID is `f-` plus a hash of the normalised text and the cited node IDs.
  - `step` is the number of finished nodes when the finding was written.
  - `effect` (`helps`, `hurts` or `neutral`) is an addition, so that support can be checked from scores (`scripts/finding_accuracy.py`).
  - The dict is a superset of the one the controller, `apply._correct` and the dashboard use.
- **What A4 sees.** Plans, operators, statuses, error categories and validation scores. No data, probe or test scores, because findings go into A3's prompt. Code, not the model, copies the cited nodes' validation and probe scores into the evidence, for monitors and C5. `coding.render_findings` shows A3 only the validation scores.
- **Phase boundary.**
  - The first boundary comes once `search.num_drafts` nodes have finished, then every `reflection.every_n` finished nodes (default 10).
  - An LLM outage leaves the boundary pending, so A4 tries again after the next node.
  - A reply still invalid after the retries is logged with a warning, and the findings stay unchanged until the next boundary. The run never crashes on a bad A4 reply.
  - At most 3 new findings come from each call, and at most `reflection.max_findings` (default 10, oldest dropped) are kept.
  - A finding that a `correct` deleted (C5 or a human) is listed in A4's prompt as removed and is never added back, even if A4 states it again. Without this, A4 re-derived the deleted finding at the next boundary in an end-to-end check, and C5, which skips findings it has already corrected, left it in place.

## Reliability and analysis scripts

Each script reads runs only through `imle.checkpoint`, writes CSVs to `--out`, and defines its measures in its docstring.

```bash
python scripts/leakage_stress_test.py --execute                     # planted leaks vs clean controls
python scripts/leakage_stress_test.py --scripts 'runs/*/nodes/*/solution.py'   # flag rate on real scripts
python scripts/finding_accuracy.py runs/*                           # unsupported / replicated findings
python scripts/analyze_val_test_gap.py --runs-dir runs              # per node, run, condition and task
python scripts/analyze_probe_fidelity.py --runs-dir runs --k 5      # probe-test Spearman and top-k
```

The leakage fixtures are one planted script and one clean control per leak type, so the stress test's rates show that the rules catch these patterns. They do not estimate performance on the agent's own scripts. For that, screen real node scripts with `--scripts` and check the flagged ones by hand.
