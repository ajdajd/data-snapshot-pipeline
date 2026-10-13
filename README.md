# Data Snapshot Pipeline

Extract figure and table snapshots from PDFs, then extract validated Schema v1.4
metadata from those images.

The pipeline runs one layout model per invocation. Snapshot extraction and
metadata extraction can be run independently or as one end-to-end command.
Submission to an external dataset or service is not implemented yet.

## Requirements

- Python 3.10 or newer
- [`uv`](https://docs.astral.sh/uv/)
- An OpenAI API key and available API credits for metadata extraction

## Installation

Install only the layout model needed for a run. For example, to use TF-ID with
metadata extraction and the development tools:

```bash
uv sync --locked --extra tfid --extra metadata --extra test
```

Replace `tfid` with one of the other layout extras when needed:

| CLI model | Dependency extra | Model weights | Inference size |
| --- | --- | --- | ---: |
| `tfid` | `tfid` | `yifeihu/TF-ID-large` | Model-defined |
| `doclayoutyolo` | `doclayoutyolo` | `juliozhao/DocLayout-YOLO-DocStructBench` | 1024 |
| `yolo11` | `yolo11` | `Armaggheddon/yolo11-document-layout` (`yolo11m_doc_layout.pt`) | 1280 |
| `yolo26` | `yolo26` | `Armaggheddon/yolo26-document-layout` (`yolo26m_doc_layout.pt`) | 1280 |

Dependencies are installed into `.venv/`. Model weights are downloaded on the
first run and cached beneath `.cache/models/`; later runs reuse the cache. TF-ID
uses a pinned model revision and stores its files beneath `.cache/models/tfid/`.

For metadata extraction, create a local environment file and add the API key:

```bash
cp .env.template .env
```

```dotenv
OPENAI_API_KEY=your-api-key
```

Both `.env` and the model cache are excluded from Git.

## Model selection

The following results are from *Benchmarking Open-Source Layout Detection
Models for Data Snapshot Extraction from Institutional Documents*. They measure
both detection and the spatial quality of matched crops across all documents in
the benchmark.

### Figures

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium |
| --- | --- | ---: | ---: | ---: | ---: |
| Detection | Precision | **0.628** | 0.547 | 0.378 | 0.388 |
|  | Recall | 0.488 | **0.802** | 0.761 | 0.721 |
| Spatial accuracy | IoU | **0.877** | 0.820 | 0.817 | 0.817 |
|  | Area precision | 0.935 | **0.996** | 0.990 | 0.990 |
|  | Area recall | **0.938** | 0.824 | 0.826 | 0.826 |

### Tables

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium |
| --- | --- | ---: | ---: | ---: | ---: |
| Detection | Precision | **0.562** | 0.468 | 0.487 | 0.460 |
|  | Recall | 0.861 | **0.893** | 0.862 | 0.891 |
| Spatial accuracy | IoU | **0.919** | 0.834 | 0.817 | 0.824 |
|  | Area precision | 0.972 | 0.993 | **0.994** | 0.994 |
|  | Area recall | **0.946** | 0.841 | 0.822 | 0.829 |

See the [benchmark paper](https://arxiv.org/abs/2606.06242) for
the dataset, evaluation protocol, corpus-level results, and limitations.

Choose based on the error profile that matters for the collection: precision
penalizes irrelevant detections, recall measures missed snapshots, and the
spatial metrics measure crop alignment and completeness. These aggregate
results are reference baselines, not a guarantee for a different document
collection.

Other layout models can be integrated with the shipped `create-adapter` skill.
For development tools that support `@` skill invocation, use:

```text
@create-adapter for {github_link}
```

Use the equivalent skill invocation in other development tools. See
[CONTRIBUTING.md](CONTRIBUTING.md#adding-a-layout-adapter) for the adapter
contract and tool-agnostic development workflow.

## Usage

Place source PDFs beneath `data/`. Commands default to the repository-root
`output/` directory and create a subdirectory for the selected model.

### End-to-end pipeline

Run snapshot extraction followed by metadata extraction:

```bash
uv run python -m data_snapshot_pipeline \
  --model=tfid \
  --input=data/example.pdf
```

### Snapshot extraction only

Run the layout model without making an OpenAI API request:

```bash
uv run python -m data_snapshot_pipeline.extract_data_snapshot \
  --model=tfid \
  --input=data/example.pdf
```

### Metadata extraction only

Process all supported images under a model's snapshot directory:

```bash
uv run python -m data_snapshot_pipeline.extract_metadata \
  --input=output/tfid/snapshots
```

When the input is a file or directory named `snapshots`, metadata is written to
its sibling `metadata` directory. For images elsewhere, pass the destination
explicitly:

```bash
uv run python -m data_snapshot_pipeline.extract_metadata \
  --input=path/to/snapshot.png \
  --output-dir=path/to/metadata
```

PDF and image directory inputs are searched recursively. Use `--help` on any
command to see all options.

## Outputs

A TF-ID run for `example.pdf` produces this layout:

```text
output/
└── tfid/
    ├── snapshots/
    │   ├── example_figure_000.png
    │   └── example_table_000.png
    └── metadata/
        ├── example_figure_000.json
        └── example_table_000.json
```

Snapshot counters are zero-based and independent for figures and tables.
Metadata files use the same stem as their snapshot.

## Existing outputs and `--force`

The PDF filename stem identifies all outputs belonging to that PDF.

- Snapshot-only and end-to-end commands skip a PDF when any matching snapshot
  or metadata file already exists. They do not load the layout model for a fully
  skipped run.
- Adding `--force` to either PDF command deletes all matching snapshots and
  metadata before starting the replacement extraction.
- Metadata-only extraction skips an image whose JSON output already exists.
  Adding `--force` replaces only that JSON file and preserves the image.

Cleanup happens before replacement work begins. If model inference or an API
request later fails, the removed outputs are not restored.

## Metadata extraction

Metadata extraction sends each snapshot image to the OpenAI Responses API and
validates the structured response against the canonical Pydantic Schema v1.4
model. The request uses only image-visible evidence; filenames, directory names,
and source-document metadata are not included as evidence.

Default request settings are in
`src/data_snapshot_pipeline/metadata_extraction/config/default.json`. Prompt
files are in the adjacent `prompts/` directory. API calls have automatic SDK
retries disabled so a failed call is not silently repeated.

## Troubleshooting

- **The first model run is slow:** model weights are being downloaded. Later
  runs reuse `.cache/models/`.
- **TF-ID prints `timm` or `GenerationMixin` warnings:** these are upstream
  compatibility warnings from the pinned TF-ID dependency stack. If extraction
  completes and prints a snapshot path, the run succeeded.
- **The API returns HTTP 429 with `insufficient_quota`:** the API key has no
  available credits. Add credits, then retry with the metadata-only command so
  the layout model does not run again.
- **A PDF is skipped:** matching outputs already exist. Keep them, or rerun the
  PDF command with `--force` to rebuild both stages.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards, verification, and
the adapter contribution workflow.
