# Contributing

Keep changes small, typed, documented, and testable without downloading model
weights or making live API requests.

## Development setup

Install the locked base environment and test tools:

```bash
uv sync --locked --extra test
```

Add only the extractor or metadata extras needed for the work. For example:

```bash
uv sync --locked --extra test --extra doclayoutyolo --extra metadata
```

Commit `uv.lock` when dependencies change. Do not commit `.env`, model weights,
input PDFs, generated snapshots, or generated metadata. These belong in the
Git-ignored `.env`, `.cache/`, `data/`, and `output/` paths.

## Coding standards

- Format Python with Black's default 88-character line length.
- Use Python 3.10+ type hints on every function signature.
- Use NumPy-style docstrings for public modules, classes, and functions.
- Follow PEP 8 naming conventions.
- Preserve lazy extractor imports so running one extractor does not require
  every extractor dependency.
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

## Adding a data snapshot extractor

Use the shipped `create-adapter` skill to apply this repository's extractor
conventions:

```text
$create-adapter for {github_link}
```

The skill source is `.agents/skills/create-adapter/SKILL.md`.

Whether using the skill or working manually, an extractor integration must:

1. Add `src/data_snapshot_pipeline/adapters/<model_name>.py` with typed,
   NumPy-documented configuration and implementation classes.
2. If multiple model sizes or variants exist, confirm the choice with the user
   before implementation. Cache downloaded weights beneath `.cache/models/`.
3. Convert model output to canonical `Detection` objects. Only `figure` and
   `table` labels are supported, and bounding boxes must be normalized to the
   inclusive unit interval.
4. Add a lazy branch to `create_adapter()` in
   `src/data_snapshot_pipeline/adapters/__init__.py`.
5. Add an extractor-specific optional dependency group to `pyproject.toml` and
   update `uv.lock` if new dependencies are required.
6. Add offline tests with an injected fake model. Tests must cover label
   mapping, normalized coordinates, thresholds, and invalid configuration.
7. Add the extractor identifier, dependency extra, weights, and inference size
   to the table in `README.md`.

`SnapshotDetector` is the internal Python protocol for snapshot extractors. Do not
add a new CLI entry point for each extractor; the existing PDF commands select
exactly one through `--model=<model_name>`.

## Pull request checklist

- The change is limited to the requested behavior.
- Public Python APIs have type hints and NumPy docstrings.
- Changed Python files pass Black.
- `uv run pytest -q`, `uv lock --check`, and `git diff --check` pass.
- Tests do not download weights or call paid APIs.
- User-owned files under `.env`, `data/`, and `output/` remain untouched.
- Documentation reflects any changed command, output, dependency, or extractor.
