"""Test model selection and model-scoped output orchestration."""

from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from data_snapshot_pipeline import Detection, run_extraction, run_pipeline
from data_snapshot_pipeline import pipeline
from data_snapshot_pipeline.adapters import create_adapter


class _FakeAdapter:
    """Return one table detection for pipeline tests."""

    def detect(self, image: Image.Image) -> list[Detection]:
        """Return a full-page table detection."""
        return [Detection("table", (0.0, 0.0, 1.0, 1.0), 0.9)]


def test_run_extraction_selects_one_model_and_scopes_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use one selected adapter and write beneath its model directory."""
    pdf_path = tmp_path / "report.pdf"
    with pymupdf.open() as document:
        document.new_page(width=72, height=72)
        document.save(pdf_path)
    selected_models: list[str] = []

    def fake_create_adapter(model_name: str) -> _FakeAdapter:
        """Record and return the selected test adapter."""
        selected_models.append(model_name)
        return _FakeAdapter()

    monkeypatch.setattr(pipeline, "create_adapter", fake_create_adapter)

    paths = run_extraction(pdf_path, tmp_path / "output", "YOLO11", dpi=72)

    assert selected_models == ["yolo11"]
    assert paths == [
        tmp_path / "output" / "yolo11" / "snapshots" / "report_table_000.png"
    ]


def test_create_adapter_rejects_unknown_model() -> None:
    """Reject an unknown model identifier."""
    with pytest.raises(ValueError, match="Unsupported model: unknown"):
        create_adapter("unknown")


def test_run_pipeline_extracts_metadata_for_available_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pass existing snapshots to model-scoped metadata extraction."""
    pdf_path = tmp_path / "report.pdf"
    with pymupdf.open() as document:
        document.new_page(width=72, height=72)
        document.save(pdf_path)
    snapshot_path = tmp_path / "output" / "tfid" / "snapshots" / "report_table_000.png"
    snapshot_path.parent.mkdir(parents=True)
    snapshot_path.write_bytes(b"existing")
    calls: list[tuple[list[Path], Path, bool, list[str]]] = []

    monkeypatch.setattr(pipeline, "create_adapter", lambda model_name: _FakeAdapter())

    def fake_extract_metadata_files(
        snapshot_paths: list[Path],
        output_dir: Path,
        *,
        force: bool,
        source_stems: list[str],
    ) -> list[Path]:
        """Record metadata orchestration without calling the API."""
        calls.append((snapshot_paths, output_dir, force, source_stems))
        return [output_dir / "report_table_000.json"]

    monkeypatch.setattr(pipeline, "extract_metadata_files", fake_extract_metadata_files)

    paths = run_pipeline(
        pdf_path,
        tmp_path / "output",
        "tfid",
        dpi=72,
        with_metadata=True,
    )

    metadata_dir = tmp_path / "output" / "tfid" / "metadata"
    assert paths == [snapshot_path, metadata_dir / "report_table_000.json"]
    assert calls == [([snapshot_path], metadata_dir, False, ["report"])]
