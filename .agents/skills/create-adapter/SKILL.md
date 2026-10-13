---
name: create-adapter
description: Add a data snapshot extractor to the Data Snapshot Pipeline from a model repository, library, or implementation link. Use for a new figure and table extractor, not metadata models or routine edits to an existing extractor.
---

# Create Adapter

Integrate one data snapshot extractor without changing the pipeline's canonical
extraction contract. Start from the supplied model or library link and reuse the
closest existing implementation in `src/data_snapshot_pipeline/adapters/`.

Before implementation, inspect `src/data_snapshot_pipeline/detection.py`,
`src/data_snapshot_pipeline/adapters/__init__.py`, the closest existing extractor
and its tests, `pyproject.toml`, and the README model table.

## Establish the model contract

Use primary sources for the model and its inference library. Confirm:

- the package and compatible version needed to load the model;
- the exact weights repository, filename, size variant, and revision;
- how to run inference on a `PIL.Image.Image`;
- the label vocabulary and which labels mean figure or table;
- bounding-box format and coordinate system;
- confidence-score availability; and
- license or remote-code requirements that affect use in this repository.

State the proposed extractor name, dependencies, cache location, and user-run
installation command. If the model offers multiple sizes or variants and the
user has not selected one, summarize the relevant quality, speed, memory, and
licensing tradeoffs and ask which checkpoint to integrate.

Cache weights under the repository-local `.cache/models/` directory. Pin a
revision whenever model loading executes repository-provided remote code.

Before installing dependencies or downloading weights, give the user the
corresponding `uv` command to run in their terminal. Proceed with installation
yourself only when the user asks you to.

## Implement the extractor

The extractor must satisfy the internal `SnapshotDetector` protocol from
`src/data_snapshot_pipeline/detection.py`:

```python
def detect(self, image: Image.Image) -> list[Detection]:
    ...
```

Each returned `Detection` must contain:

- label `"figure"` or `"table"`;
- normalized `(x1, y1, x2, y2)` coordinates in `[0, 1]` with positive area;
  and
- a confidence score in `[0, 1]`.

Ignore unsupported labels and invalid or undersized boxes. Use the existing
minimum normalized area of `0.008` unless the model has a documented reason for
another value. Clamp coordinates and scores at the extractor boundary.

Follow the existing implementation structure:

1. Add `src/data_snapshot_pipeline/adapters/<model_name>.py`.
2. Define model identifiers, filenames, and cache paths as module constants.
3. Use a frozen dataclass for validated model configuration.
4. Support injected model objects, and processors when applicable, so tests do
   not load weights.
5. Keep imports for optional model libraries inside model-loading functions.
6. Add a lazy branch to `create_adapter()` in
   `src/data_snapshot_pipeline/adapters/__init__.py`.
7. Add an extractor-specific optional dependency group to `pyproject.toml` and
   update `uv.lock`.

Do not add an extractor-specific CLI. Both PDF commands already select exactly
one extractor through `--model=<model_name>`.

## Test offline

Add `tests/test_<model_name>.py` using an injected fake model. Cover the logic
specific to the integration:

- raw-to-canonical label mapping;
- coordinate normalization and clamping;
- score clamping or the documented fallback score;
- invalid and undersized detection filtering;
- configuration validation;
- selected checkpoint and local cache defaults; and
- cached-weight loading without contacting the model hub, when practical.

Never make model downloads or live API calls during tests. Format changed
Python files individually, then verify:

```bash
uv run --no-sync pytest -q
uv lock --check
git diff --check
```

Run a real model smoke test only when the user authorizes the download and local
output changes. Otherwise provide the exact snapshot-only command for the user
to run.

## Finish the integration

Update the model table and selection guidance in `README.md`. Report the model
source, selected weights, new dependency extra, offline test result, and any
unperformed live smoke test.
