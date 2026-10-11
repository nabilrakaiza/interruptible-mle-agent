# Core agent: assumptions about other roles

Written 11 Oct 2026 by role 2. The controller (`controller.py`) and coding agent (`agents/coding.py`) were built before the modules they depend on existed, so each interface below is a guess. **None of these is agreed yet.** If you own one and want it different, say so; the change on the role 2 side is small.

The controller takes the sandbox, LLM and evaluator as arguments, and `tests/test_controller.py` runs the whole loop with fakes. Return types are matched by attribute name, so a dataclass or a pydantic model both work and nothing needs to be imported from role 2.

## Role 1: sandbox (`sandbox.py`)

```python
def run(script_path: Path, cwd: Path, timeout_s: float) -> ExecResult
# ExecResult has: stdout: str, stderr: str, exit_code: int, wall_time_s: float, timed_out: bool
```

- Runs `script_path` with `cwd` as the working directory, and kills it after `timeout_s`. A timeout returns a result with `timed_out=True`; it does not raise.
- The controller creates the node directory `runs/<run_id>/nodes/<node_id>/`, writes `solution.py` into it, and symlinks `input` to the evaluator's input directory. This works for a subprocess sandbox. A Docker sandbox would mount the input directory at `<cwd>/input` instead, and the controller's symlink line goes away.
- The Python environment has numpy, pandas, scipy and scikit-learn. The prompt tells the model it may use exactly these (`PACKAGES` in `agents/coding.py`). Tell role 2 when the list is final, for example if lightgbm, xgboost or torch are added.

## Role 1: LLM wrapper (`llm_log.py`)

```python
def complete(agent: str, system: str, user: str, *, model: str, temperature: float, seed: int, run_dir: Path) -> str
```

- Returns the completion text and logs the call to `run_dir/llm_calls.jsonl`.
- Retries on transient API errors happen inside the wrapper. An exception that escapes it ends the run.
- `model` and `temperature` come from `llm:` in the config. The controller binds them once, so agents call `llm(agent=..., system=..., user=...)`.
- The provider and the value of `LLM_MODEL` are role 1's choice.

## Role 1: grading

- Not wired in yet. `test_score` stays empty until there is a grading function to call.
- Each scored node keeps its test-set submission at `nodes/<node_id>/submission.csv` (written by the evaluator, see below), so nodes can be graded after the run as well as during it.
- The final submission is copied to `runs/<run_id>/submission.csv`.

## Role 3: evaluator (`agents/evaluation.py`)

```python
def prepare(task: str, run_dir: Path, seed: int) -> TaskContext
# TaskContext has: description: str, input_dir: Path, prediction_format: str,
#                  metric: str, higher_is_better: bool

def score(node_dir: Path) -> ScoreResult
# ScoreResult has: val_score: float | None, probe_score: float | None, error: str | None
```

The script contract, which is the part that most needs agreement:

- `input_dir` holds `train.csv` (labelled) and `predict.csv` (unlabelled), plus any other files the task needs, such as image folders. The script sees it as `./input`.
- `predict.csv` is the validation, probe and test rows mixed together, with no column saying which is which.
- The script writes one file, `./predictions.csv`, covering every row of `predict.csv`. `prediction_format` is one or two sentences telling the model what that file must contain, for example the column names and whether values are probabilities.
- `score(node_dir)` reads `node_dir/predictions.csv`, splits it by row ID, scores validation and probe, and writes the test rows to `node_dir/submission.csv` in the competition's submission format.
- If the file is missing or malformed, `score` returns `error` set to a short reason and does not raise.

Why this shape: the holdout labels never enter the sandbox, the script cannot tell probe rows from validation rows, and one output file covers scoring and the test submission.

This differs from the proposal, which says the script "scores itself through the harness". Here the harness scores the script from outside. If role 3 prefers the proposal's version, the prompt template and the fake evaluator in the tests are what change.

Not covered yet: the leakage screen before execution, and what the script does when `agents.evaluation` is false (A1-off).

## Role 4: checkpoint and interventions

- A checkpoint is written after `prepare` with an empty tree (step 0), after every node, and once more at the end.
- `status.json` contains `current_node`, `elapsed_s`, `timestamp`, `task`, `seed`, `condition` and `done`. `current_node` is the node that just finished, or null at step 0 and at the end.
- The final checkpoint has `done: true` and adds `stop_reason` (`budget`, `max_nodes` or `search_exhausted`), `final_node` and `submitted`.
- Per-node files are outside the checkpoint, in `runs/<run_id>/nodes/<node_id>/`: `solution.py`, `stdout.txt`, `stderr.txt`, `predictions.csv`, `submission.csv`.
- Interventions are not applied yet. The controller will call the apply function from `safe_point()`.

## Decisions inside role 2

Stated here because they affect how runs are read.

- `Node.error` starts with a category: `generation_error`, `timeout`, `runtime_error` or `invalid_submission`. The last three map onto the error taxonomy in `experiments.md`. `generation_error` is new: the model returned no code block twice in a row.
- Node IDs are `n0`, `n1`, ... in creation order.
- The budget clock starts before `prepare`, and time spent waiting on the LLM counts.
- A script's timeout is `script_timeout_s` or the remaining budget, whichever is smaller.
- Until debug and improve exist, the search stops after `num_drafts` drafts with `stop_reason: search_exhausted`.
