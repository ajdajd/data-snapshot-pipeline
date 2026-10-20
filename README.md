# Data Snapshot Pipeline

Extract figure and table snapshots from PDFs, then extract validated Schema v1.4
metadata from those images.

The pipeline runs one data snapshot extractor per invocation. Snapshot
extraction and metadata extraction can run independently or as one end-to-end
command.
Submission to an external dataset or service is not implemented yet.

## Requirements

- Python 3.10 or newer
- [`uv`](https://docs.astral.sh/uv/)
- An OpenRouter or OpenAI API key with available credits for metadata extraction

## Installation

Install only the extractor needed for a run. The examples use DocLayout-YOLO
with metadata extraction:

```bash
uv sync --locked --extra doclayoutyolo --extra metadata
```

Replace `doclayoutyolo` with another extractor extra when needed:

| Extractor | Dependency extra | Model weights | Inference size |
| --- | --- | --- | ---: |
| `doclayoutyolo` | `doclayoutyolo` | `juliozhao/DocLayout-YOLO-DocStructBench` | 1024 |
| `tfid` | `tfid` | `yifeihu/TF-ID-large` | Model-defined |
| `yolo11` | `yolo11` | `Armaggheddon/yolo11-document-layout` (`yolo11m_doc_layout.pt`) | 1280 |
| `yolo26` | `yolo26` | `Armaggheddon/yolo26-document-layout` (`yolo26m_doc_layout.pt`) | 1280 |

Model weights are downloaded on the first run and cached beneath `.cache/models/`; later runs reuse the cache.

See [Model selection](#model-selection) for more information.

### Metadata API setup

Required for end-to-end and metadata-only runs. Skip this step for snapshot
extraction only.

Create `.env` from the template if you have not already done so, then set the key
for your chosen provider:

```bash
cp .env.template .env
```

| Provider | Environment variable | CLI selection | Configuration |
| --- | --- | --- | --- |
| OpenRouter (default) | `OPENROUTER_API_KEY` | `--metadata-provider=openrouter` | [`openrouter.json`](src/data_snapshot_pipeline/metadata_extraction/config/openrouter.json) |
| OpenAI | `OPENAI_API_KEY` | `--metadata-provider=openai` | [`openai.json`](src/data_snapshot_pipeline/metadata_extraction/config/openai.json) |

Both keys may be present. Add `--metadata-provider=openai` to either command that
extracts metadata to use OpenAI directly.

Both packaged configurations use GPT-5.6 Luna. In both end-to-end and
metadata-only runs, each snapshot is sent to the selected provider's Responses
API, and the structured response is validated against the canonical Pydantic
Schema v1.4 model before saving. Requests use only image-visible evidence;
filenames, directory names, and source-document metadata are excluded. See the
[prompt files](src/data_snapshot_pipeline/metadata_extraction/prompts/) for the
extraction instructions. Automatic SDK retries are disabled.

## Usage

Run these commands from the repository root after installation. The end-to-end
and snapshot-only commands use one extractor selected with `--model`; `--input`
accepts a PDF or a directory searched recursively for PDFs. Inputs may live
anywhere; the examples use `data/`.

Add `--help` to any command to see its options.

### End-to-end pipeline

Run snapshot extraction followed by metadata extraction:

```bash
uv run --no-sync python -m data_snapshot_pipeline \
  --model=doclayoutyolo \
  --input=data/example.pdf
```

### Snapshot extraction only

Run the selected extractor without making a metadata API request:

```bash
uv run --no-sync python -m data_snapshot_pipeline.extract_data_snapshot \
  --model=doclayoutyolo \
  --input=data/example.pdf
```

### Metadata extraction only

Extract metadata from existing snapshots, including after a failed metadata
stage, without rerunning the PDF extractor:

```bash
uv run --no-sync python -m data_snapshot_pipeline.extract_metadata \
  --input=output/doclayoutyolo/snapshots
```

The input may be a PNG, JPEG, GIF, or WebP image, or a directory searched
recursively for those images. When the input directory is named `snapshots`, or
an input image is directly inside one, the destination defaults to its sibling
`metadata` directory. For inputs elsewhere, `--output-dir` is required:

```bash
uv run --no-sync python -m data_snapshot_pipeline.extract_metadata \
  --input=path/to/snapshot.png \
  --output-dir=path/to/metadata
```

### Output files

The end-to-end and snapshot-only commands write beneath `output/<model>/` by
default, relative to the current working directory. Use `--output-dir` to choose
a different output root. An end-to-end DocLayout-YOLO run for `example.pdf`
produces files like these:

```text
output/
└── doclayoutyolo/
    ├── snapshots/
    │   ├── example_figure_000.png
    │   └── example_table_000.png
    └── metadata/
        ├── example_figure_000.json
        └── example_table_000.json
```

Snapshot counters are zero-based and independent for figures and tables.
Each JSON file contains validated metadata and uses the same stem as its
snapshot. PDF stems must be unique within a run, even across input subdirectories.

### Rerunning and replacing outputs

Existing outputs are identified by filename. The end-to-end and snapshot-only
commands match files belonging to each PDF stem within the selected extractor's
output directory; metadata-only runs check for a JSON file with the image's stem
in the destination directory.

| Command | Default behavior | With `--force` (or `-f`) |
| --- | --- | --- |
| End-to-end | Skip the entire PDF if any matching snapshot or metadata exists. | Delete matching snapshots and metadata, then rerun both stages. |
| Snapshot-only | Skip the entire PDF if any matching snapshot or metadata exists. | Delete matching snapshots and metadata, then extract snapshots only. |
| Metadata-only | Skip images whose JSON output already exists. | Delete and regenerate each existing JSON output, preserving the images. |

The end-to-end and snapshot-only commands skip partial outputs too; they do not
resume missing metadata. Use the metadata-only command above to generate missing
JSON files. A fully skipped run does not load the extractor.

**`--force` deletes existing outputs before replacement work begins.** If
inference or an API request fails, deleted files are not restored. This also
applies to metadata-only replacement of an existing JSON file.

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

See the [benchmark paper](https://arxiv.org/abs/2606.06242) for the dataset,
evaluation protocol, corpus-level results, and limitations.

Choose based on the error profile that matters for the collection: precision
penalizes irrelevant detections, recall measures missed snapshots, and the
spatial metrics measure crop alignment and completeness. These aggregate
results are reference baselines, not a guarantee for a different document
collection.

### Other models

Other data snapshot extractors can be integrated with the shipped
`create-adapter` skill:

```text
$create-adapter for {github_link}
```

See [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-data-snapshot-extractor) for the
extractor contract.

## Troubleshooting

- **The first extractor run is slow:** model weights are being downloaded. Later
  runs reuse `.cache/models/`.
- **TF-ID prints `timm` or `GenerationMixin` warnings:** these are upstream
  compatibility warnings from the pinned TF-ID dependency stack. If extraction
  completes and prints a snapshot path, the run succeeded.
- **The API returns HTTP 429:** free-model rate limits or paid-provider quota may
  be exhausted. Retry later or add credits, then use the metadata-only command
  so the snapshot extractor does not run again.
- **A PDF is skipped:** matching outputs already exist. Keep them, or rerun the
  end-to-end command with `--force` to rebuild both stages.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards, verification, and
the extractor contribution workflow.
