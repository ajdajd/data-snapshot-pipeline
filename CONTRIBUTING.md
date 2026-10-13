# Contributing

Keep changes small, typed, documented, and testable without downloading model
weights or making live API requests.

## Development setup

Install the locked base environment and test tools:

```bash
uv sync --locked --extra test
```

Add only the model or metadata extras needed for the work. For example:

```bash
uv sync --locked --extra test --extra tfid --extra metadata
```

Commit `uv.lock` when dependencies change. Do not commit `.env`, model weights,
input PDFs, generated snapshots, or generated metadata. These belong in the
Git-ignored `.env`, `.cache/`, `data/`, and `output/` paths.

## Coding standards

- Format Python with Black's default 88-character line length.
- Use Python 3.10+ type hints on every function signature.
- Use NumPy-style docstrings for public modules, classes, and functions.
- Follow PEP 8 naming conventions.
- Preserve lazy adapter imports so running one model does not require every
  model dependency.
- Keep tests offline by injecting fake model, processor, or API clients.

## Verification

Format each changed Python file:

```bash
uv run black path/to/changed_file.py
```

Then run the offline test suite and lock-file check:

```bash
uv run pytest -q
uv lock --check
git diff --check
```

Do not use a live metadata request as an automated test. When a manual smoke
test is necessary, state that it consumes API credits before running it.

## Adding a layout adapter

Use the shipped `create-adapter` skill to apply this repository's adapter
conventions:

```text
$create-adapter for {github_link}
```

The skill source is `.agents/skills/create-adapter/SKILL.md`.

Whether using the skill or working manually, an adapter change must:

1. Add `src/data_snapshot_pipeline/adapters/<model_name>.py` with typed,
   NumPy-documented configuration and adapter classes.
2. Use medium model weights unless the project explicitly chooses another
   size, and cache downloaded weights beneath `.cache/models/`.
3. Convert model output to canonical `Detection` objects. Only `figure` and
   `table` labels are supported, and bounding boxes must be normalized to the
   inclusive unit interval.
4. Add a lazy branch to `create_adapter()` in
   `src/data_snapshot_pipeline/adapters/__init__.py`.
5. Add a model-specific optional dependency group to `pyproject.toml` and
   update `uv.lock` if new dependencies are required.
6. Add offline tests with an injected fake model. Tests must cover label
   mapping, normalized coordinates, thresholds, and invalid configuration.
7. Add the model identifier, dependency extra, weights, and inference size to
   the table in `README.md`.

Do not add a new CLI entry point for each model. The existing PDF commands take
exactly one model through `--model=<model_name>`.

## Pull request checklist

- The change is limited to the requested behavior.
- Public Python APIs have type hints and NumPy docstrings.
- Changed Python files pass Black.
- `uv run pytest -q`, `uv lock --check`, and `git diff --check` pass.
- Tests do not download weights or call paid APIs.
- User-owned files under `.env`, `data/`, and `output/` remain untouched.
- Documentation reflects any changed command, output, dependency, or adapter.
