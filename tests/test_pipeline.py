"""Test model selection and model-scoped output orchestration."""

from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from data_snapshot_pipeline import Detection, run_extraction
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
