# Core agent: assumptions about other roles

Started 11 Oct 2026 by role 2, updated 18 Oct. The controller (`controller.py`) and coding agent (`agents/coding.py`) were built before most of the modules they depend on existed, so several interfaces below are guesses. Each section says whether it is **built on real code** or **assumed**. If you own an assumed one and want it different, say so; the change on the role 2 side is small.

The controller takes the sandbox, LLM, evaluator and reflection agent as arguments, and the tests run the whole loop with fakes. Return types are matched by attribute name, so a dataclass or a pydantic model both work and nothing needs to be imported from role 2.

## Run folder layout

```
runs/<run_id>/
  config.yaml              merged config, written before prepare()
  task_context.json        what prepare() returned, so a resumed run does not rebuild the splits
  workspace/               the sandbox's working directory, read-only to scripts
    input/                 hard-linked copy of the evaluator's input folder
    n0.py, n1.py, ...      each node's script as executed (OUTPUT_DIR line first)
  nodes/<node_id>/
    solution.py            the script as the model wrote it
    output/predictions.csv written by the script
    stdout.txt, stderr.txt
    submission.csv         written by the evaluator's score()
  checkpoints/<step>/      tree.json, findings.json, status.json
  queue.jsonl, applied.jsonl, llm_calls.jsonl
  submission.csv           the final submission (final/submission_<rank>.csv too for top_k)
```

## Role 1: sandbox (built on Medhini's `imle.sandbox.run_script`, branch `medhini-infrastructure`)

```python
def run_script(script_path, task_dir, timeout_s=3600, image="python:3.11-slim",
               harness_dir=None, output_dir=None) -> SandboxResult
# SandboxResult has: stdout, stderr, exit_code, wall_time_s, timed_out
```

**What it does:** runs one script in a fresh Docker container with no network, the task folder mounted read-only at `/workspace` and the output folder writable at `/output`, and kills it after `timeout_s`.

`imle/execution.py` wraps it as `DockerSandbox`. The task folder is the run's `workspace/` and the output folder is the node's `output/`. Each script gets `OUTPUT_DIR = "/output"` as its first line. `SubprocessSandbox` does the same without Docker, for local testing only; choose it with `sandbox.backend: subprocess` or `--sandbox subprocess`.

Tested against her branch in a test merge: everything works, and the only conflict is a trivial one in `.gitignore`. I could not run Docker on my machine.

Still assumed:

- **A Docker image with the packages.** `python:3.11-slim` has no numpy, pandas or scikit-learn, and the container has no network, so every script would fail on import. The controller uses `sandbox.image` (default `imle-sandbox:latest`). Role 1 needs to build that image, for example from:

  ```dockerfile
  FROM python:3.11-slim
  RUN pip install --no-cache-dir numpy pandas scipy scikit-learn pillow
  ```

  The prompt tells the model it may use exactly these packages (`PACKAGES` in `agents/coding.py`). Tell role 2 if lightgbm, xgboost or torch are added.
- **Output folder permissions.** The container runs as uid 65534. On Linux it cannot write to a host folder with mode 755, so `DockerSandbox` makes each node's output folder world-writable before the run.
- **Abandon.** `run_script` names its container internally, so the controller cannot call `abandon_experiment` on a running node. This is fine because abandon is cut from scope.

## Role 1: LLM logging (built on Medhini's `imle.llm_log.log_llm_call`)

```python
def log_llm_call(run_id, agent, model, prompt, completion, input_tokens, output_tokens,
                 latency_s, seed=None, sampling_params=None, cost_usd=None, runs_dir="runs")
```

**What it does:** appends one record per LLM call to `runs/<run_id>/llm_calls.jsonl`.

Her branch has the logger but no API client, so role 2 wrote one in `imle/llm.py` (`AnthropicLLM`). It calls `log_llm_call` when that function exists, and writes an identical record itself until the branch is merged.

Assumed, as the provider is not decided:

- **Model:** Claude through the Anthropic SDK (`anthropic` added to `pyproject.toml`). The model comes from `LLM_MODEL` and defaults to `claude-opus-5-5` when that is unset. Credentials come from `ANTHROPIC_API_KEY` in `.env`, or from an `ant auth login` profile.
- **Effort and temperature:** `llm.effort` (default `high`) sets reasoning depth. `llm.temperature` is not sent, because current Claude models reject sampling parameters.
- **Refusal fallback:** requests opt into server-side refusal fallback (`fallbacks: "default"`), so a declined request is retried on another model instead of failing. The model that actually answered is the one logged.
- **Errors and retries:** the SDK retries transient errors 5 times. An error that still escapes ends the run, which can then be resumed with `--resume`.
- **Cost:** `cost_usd` is filled in for Opus 5.5, Sonnet 5.5 and Haiku 5.5, and left empty for any other model.

## Role 1: grading and launching

- `test_score` stays empty. Each scored node keeps its test submission at `nodes/<node_id>/submission.csv`, so grading can happen after the run.
- **Resume:** `python -m imle.controller --resume runs/<run_id>` continues a crashed run from its last complete checkpoint. The node that was running is moved to `nodes/_unfinished/`. Time between the crash and the resume is not charged to the budget.
- **Scripted monitors:** the controller does not start the scripted monitors for C4 and C5 (`monitors:` in the config). It only reads `queue.jsonl`, so the launcher has to start each policy as its own process.

## Role 3: evaluator (`agents/evaluation.py`, assumed: nothing pushed yet)

```python
def prepare(task: str, run_dir: Path, seed: int) -> TaskContext
# TaskContext has: description: str, input_dir: Path, prediction_format: str,
#                  metric: str, higher_is_better: bool

def score(node_dir: Path) -> ScoreResult
# ScoreResult has: val_score: float | None, probe_score: float | None, error: str | None

def screen(llm, script: str) -> str | None      # optional
```

**What they do:**

- `prepare` runs once at the start of a run. It builds the train, validation and probe splits and returns what the coding agent needs: the task description, the input folder, the prediction format and the metric. It can read `run_dir/config.yaml`, for example to switch behaviour for A1-off.
- `score` runs once per node, after its script has finished. It reads `node_dir/output/predictions.csv`, scores validation and probe, and writes the test rows to `node_dir/submission.csv`. Missing or malformed predictions come back as `error`; it never raises. It must also work in a new process after a crash, using only what `prepare` saved under the run folder.
- `screen`, if it exists and `agents.evaluation` is on, checks a script before it runs. A returned reason marks the node buggy with `leakage: <reason>`, and the script is never executed.

The script contract, which is the part that most needs agreement:

- `input_dir` holds `train.csv` (labelled) and `predict.csv` (unlabelled), plus any other files the task needs, such as image folders. The controller hard-links it into `workspace/input`, and the script sees it as `./input`.
- `predict.csv` is the validation, probe and test rows mixed together, with no column saying which is which.
- The script writes `os.path.join(OUTPUT_DIR, "predictions.csv")`, covering every row of `predict.csv`. `prediction_format` is one or two sentences telling the model what that file must contain.

Why this shape: the holdout labels never enter the sandbox, the script cannot tell probe rows from validation rows, and one output file covers scoring and the test submission. This differs from the proposal, which says the script "scores itself through the harness". If role 3 prefers that version, the prompt template and the fake evaluator in the tests are what change.

Without `prepare` and `score` the controller's command line exits with a message saying so.

## Role 3: reflection (`agents/reflection.py`, assumed: nothing pushed yet)

```python
def reflect(llm, tree: Tree, findings: list[dict], run_dir: Path) -> list[dict]
```

**What it does:** called after every node. It returns the findings unchanged, or updated if the node closed a phase; deciding what counts as a phase boundary is up to role 3.

- **Finding format:** `{"id": "f1", "text": "...", "evidence": [{"node_id": "n3", "val_score": 0.41}]}`. The prompt shows the ID, the text and the evidence, and `correct` interventions find findings by `id`.
- **When it is missing:** the run continues without findings and prints a warning.
- **A4-off:** with `agents.reflection: false` it is never called and no findings reach the prompt.

## Role 4: interventions (stand-in in `imle/apply.py`)

```python
def apply_pending(run_dir: Path, tree: Tree, findings: list[dict], state: SearchState) -> list[AppliedRecord]
```

**What it does:** at a safe point, applies or drops every queued intervention not yet handled, in timestamp order, and appends each outcome to `applied.jsonl` with a reason.

Nothing from role 4 was pushed, so role 2 wrote this to the protocol in `intervention-protocol.md`. Role 4 owns it and can rewrite it freely; keep the signature or tell role 2. How each action is handled:

| Action | Applied when | Effect |
|---|---|---|
| `prune` | target node exists and is not already pruned | the node and its subtree become `pruned`; a redirect or override pointing into it is cancelled |
| `redirect` | `params.operator` is draft (no target needed), debug on a buggy node with a script, or improve on a working node | that becomes the next node |
| `override` | target is working | that node is submitted, whatever `final_selection` says |
| `inject` | `params.card` is text or an object | added to the model cards in every later prompt, delimited as untrusted |
| `correct` | the finding ID exists | finding deleted, or its text replaced by `params.replacement` |
| `rebudget` | `params.seconds` is a number | added to the wall-clock budget |
| `abandon` | never | dropped (scope cut) |

If anything was applied, the controller writes a second checkpoint straight away, so monitors see the effect without waiting for the next node. A malformed line in `queue.jsonl` makes `intervention.read_all` raise. `apply_pending` catches that and skips the safe point instead of crashing the run, but the bad line then blocks the queue until it is removed. Role 4 should make `read_all` skip bad lines.

## Role 4: checkpoint contents

- **When:** a checkpoint is written after `prepare` (step 0, empty tree), after every node, again after any applied intervention, and once at the end.
- **`status.json` fields:**
  - `current_node`: the node that just finished.
  - `elapsed_s` and `remaining_s`.
  - `timestamp`, `task`, `seed`, `condition` and `done`.
  - `search`: the controller's own state (rebudgets, override, pending redirect, injected cards, random state).
- **Final checkpoint:** adds `stop_reason` (`budget` or `max_nodes`), `final_selection` (`best_val`, `top_k` or `override`, plus a note if an override fell back), `final_node`, `final_nodes` and `submitted`.
- **Resume:** checkpoint folders left half-written by a crash are renamed to `_incomplete_<step>`. Otherwise `checkpoint.read` would keep returning nothing after a resume.

## Decisions inside role 2

Stated here because they affect how runs are read.

- **Selection:** the AIDE-style greedy policy, with the values in `configs/base.yaml`.
  - Draft until there are `num_drafts` drafts, counting failed and pruned ones.
  - Then, with probability `debug_prob`, debug a random buggy leaf. A chain of debug attempts stops at `max_debug_depth`.
  - Otherwise improve the best working node.
  - A node stops being improved once `improve_patience` of its improve children have failed to beat it by `improve_min_rel_gain`, relative to its score. A buggy improve child counts as a failure.
  - With nothing to improve, debug if possible, else draft again. The search therefore ends only on budget or node cap.
- **Final selection:** `best_val` takes the best working node by validation score. `top_k` takes the best `top_k` (default 3) and also writes `final/submission_<rank>.csv`. An applied `override` wins in every mode.
- **Error categories:** `Node.error` starts with `generation_error`, `leakage`, `timeout`, `runtime_error` or `invalid_submission`. `generation_error` means the model returned no code block twice in a row; the others map onto the taxonomy in `experiments.md`.
- **Model cards:** the hand-written cards that replace A2 are in `agents/retrieval.py`, a few per modality, using only the sandbox packages. `agents.retrieval: false` turns them off. Injected cards are always shown.
- **Node files:** IDs are `n0`, `n1`, ... in creation order, and `Node.script_path` is relative to the run folder.
- **Budget:** the clock starts before `prepare`, and time waiting on the LLM counts. A script's timeout is `script_timeout_s` or the remaining budget, whichever is smaller.
- **Config keys added to `configs/base.yaml`:** `top_k`, `llm.effort`, `llm.max_tokens` and `sandbox.backend` / `sandbox.image`.
