# Contributing

## Workflow

- `main` stays runnable. Work on branches named `<name>/<short-topic>`, for example `nabil/queue-schema`.
- Open a pull request and get one review from another member before merging.
- Keep pull requests small. One component or one fix per PR.

## Hard rules

1. **No data in git.** Anything under `data/` is ignored for a reason.
2. **No keys in git.** Use `.env`. If a key is ever committed, rotate it immediately; deleting the commit is not enough.
3. **Don't change a shared contract silently.** `tree.py`, `intervention.py`, and `checkpoint.py` are used by everyone. Changes to them need a PR that says what changed and why.
4. **Log everything the agent does.** Every LLM call records prompt, completion, model version, sampling parameters, tokens, and timestamp. We can't reproduce runs exactly, so logs are the evidence.

## Before pushing

```bash
ruff check src tests
pytest
```

## Contribution tracking

The final report needs a contribution statement. Keep a short line per week in `docs/contributions.md` of what you did. It takes a minute and saves an argument later.
