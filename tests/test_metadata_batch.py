"""Test writing validated snapshot metadata files."""

import json
from pathlib import Path

import pytest

from data_snapshot_pipeline.metadata_extraction import ExtractionResult
from data_snapshot_pipeline.metadata_extraction import batch
from data_snapshot_pipeline.metadata_schema import DataSnapshotMetadata


def _result(title: str) -> ExtractionResult:
    """Build a successful extraction result for a test."""
    return ExtractionResult(
        metadata=DataSnapshotMetadata(title=title),
        model="test-model",
        response_id="resp_test",
        api_status="completed",
        incomplete_details=None,
        elapsed_seconds=0.1,
        usage=None,
        raw_output=None,
        error_type=None,
        error=None,
    )


def test_extract_metadata_files_writes_validated_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Write one canonical JSON file beside the model's snapshots directory."""
    snapshot_path = tmp_path / "snapshots" / "report_table_000.png"
    snapshot_path.parent.mkdir()
    snapshot_path.write_bytes(b"image")
    monkeypatch.setattr(batch, "extract_metadata", lambda path: _result("A title"))

    paths = batch.extract_metadata_files([snapshot_path], tmp_path / "metadata")

    assert paths == [tmp_path / "metadata" / "report_table_000.json"]
    assert json.loads(paths[0].read_text(encoding="utf-8"))["title"] == "A title"


def test_extract_metadata_files_skips_existing_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Preserve an existing JSON file without making an API request."""
    snapshot_path = tmp_path / "snapshots" / "report_table_000.png"
    metadata_path = tmp_path / "metadata" / "report_table_000.json"
    snapshot_path.parent.mkdir()
    metadata_path.parent.mkdir()
    snapshot_path.write_bytes(b"image")
    metadata_path.write_text('{"keep": true}\n', encoding="utf-8")

    def fail_if_called(path: Path) -> ExtractionResult:
        """Fail if the skipped snapshot reaches extraction."""
        raise AssertionError(f"Unexpected extraction call: {path}")

    monkeypatch.setattr(batch, "extract_metadata", fail_if_called)

    paths = batch.extract_metadata_files([snapshot_path], tmp_path / "metadata")

    assert paths == [metadata_path]
    assert metadata_path.read_text(encoding="utf-8") == '{"keep": true}\n'
    assert "existing metadata found" in capsys.readouterr().out


def test_force_replaces_current_and_removes_stale_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replace current JSON and remove stale outputs for the same source PDF."""
    snapshot_path = tmp_path / "snapshots" / "report_table_000.png"
    metadata_dir = tmp_path / "metadata"
    metadata_path = metadata_dir / "report_table_000.json"
    stale_path = metadata_dir / "report_figure_999.json"
    unrelated_path = metadata_dir / "other_table_000.json"
    prefix_neighbor = metadata_dir / "report_figure_2024_table_000.json"
    snapshot_path.parent.mkdir()
    metadata_dir.mkdir()
    snapshot_path.write_bytes(b"image")
    for path in (metadata_path, stale_path, unrelated_path, prefix_neighbor):
        path.write_text('{"old": true}\n', encoding="utf-8")
    monkeypatch.setattr(batch, "extract_metadata", lambda path: _result("New title"))

    batch.extract_metadata_files(
        [snapshot_path],
        metadata_dir,
        force=True,
        source_stems=["report"],
    )

    assert json.loads(metadata_path.read_text(encoding="utf-8"))["title"] == "New title"
    assert not stale_path.exists()
    assert unrelated_path.exists()
    assert prefix_neighbor.exists()


def test_extraction_failure_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Raise a useful error without creating invalid metadata JSON."""
    snapshot_path = tmp_path / "snapshots" / "report_table_000.png"
    snapshot_path.parent.mkdir()
    snapshot_path.write_bytes(b"image")
    failure = ExtractionResult(
        metadata=None,
        model="test-model",
        response_id="resp_failed",
        api_status="incomplete",
        incomplete_details={"reason": "max_output_tokens"},
        elapsed_seconds=0.1,
        usage=None,
        raw_output="{",
        error_type="ValueError",
        error="Response was incomplete: max_output_tokens.",
    )
    monkeypatch.setattr(batch, "extract_metadata", lambda path: failure)

    with pytest.raises(RuntimeError, match="max_output_tokens"):
        batch.extract_metadata_files([snapshot_path], tmp_path / "metadata")

    assert not (tmp_path / "metadata").exists()
