"""Run the production data snapshot extraction pipeline."""

from data_snapshot_pipeline.detection import Detection, LayoutAdapter
from data_snapshot_pipeline.extraction import extract_snapshots
from data_snapshot_pipeline.inputs import discover_pdfs
from data_snapshot_pipeline.metadata_extraction import (
    ExtractionResult,
    extract_metadata,
)
from data_snapshot_pipeline.metadata_schema import DataSnapshotMetadata
from data_snapshot_pipeline.naming import build_snapshot_stem
from data_snapshot_pipeline.pipeline import run_extraction
from data_snapshot_pipeline.rendering import iter_pdf_pages
from data_snapshot_pipeline.submission import submit_snapshot

__all__ = [
    "Detection",
    "DataSnapshotMetadata",
    "ExtractionResult",
    "LayoutAdapter",
    "build_snapshot_stem",
    "discover_pdfs",
    "extract_snapshots",
    "extract_metadata",
    "iter_pdf_pages",
    "run_extraction",
    "submit_snapshot",
]
