"""Test snapshot detection and cropping orchestration."""

from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from data_snapshot_pipeline import Detection, extract_snapshots


class _FakeAdapter:
    """Return fixed detections for extraction tests."""

    def detect(self, image: Image.Image) -> list[Detection]:
        """Return intentionally unordered figure and table detections."""
        return [
            Detection("figure", (0.5, 0.5, 1.0, 1.0), 0.8),
            Detection("table", (0.0, 0.0, 0.5, 0.5), 0.9),
            Detection("figure", (0.0, 0.0, 0.5, 0.5), 0.7),
        ]


def _write_pdf(path: Path) -> None:
    """Write one 72-point square PDF page for a test."""
    with pymupdf.open() as document:
        document.new_page(width=72, height=72)
        document.save(path)


def test_extract_snapshots_saves_spatially_ordered_zero_based_names(
    tmp_path: Path,
) -> None:
    """Crop from one render and assign independent label counters."""
    pdf_path = tmp_path / "report.pdf"
    _write_pdf(pdf_path)

    paths = extract_snapshots(pdf_path, tmp_path / "output", _FakeAdapter(), dpi=72)

    assert [path.name for path in paths] == [
        "report_table_000.png",
        "report_figure_000.png",
        "report_figure_001.png",
    ]
    assert [Image.open(path).size for path in paths] == [
        (36, 36),
        (36, 36),
        (36, 36),
    ]


def test_extract_snapshots_refuses_to_overwrite(tmp_path: Path) -> None:
    """Preserve an existing snapshot instead of replacing it."""
    pdf_path = tmp_path / "report.pdf"
    _write_pdf(pdf_path)
    existing = tmp_path / "output" / "snapshots" / "report_table_000.png"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"keep")

    with pytest.raises(FileExistsError, match="Snapshot already exists"):
        extract_snapshots(pdf_path, tmp_path / "output", _FakeAdapter(), dpi=72)

    assert existing.read_bytes() == b"keep"


def test_extract_snapshots_rejects_duplicate_document_stems(tmp_path: Path) -> None:
    """Reject recursive inputs that would produce colliding output names."""
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    _write_pdf(first_dir / "report.pdf")
    _write_pdf(second_dir / "report.pdf")

    with pytest.raises(ValueError, match="filename stems must be unique"):
        extract_snapshots(tmp_path, tmp_path / "output", _FakeAdapter(), dpi=72)
