"""Test the snapshot extraction command-line interface."""

from pathlib import Path

import pytest

from data_snapshot_pipeline import cli


def test_main_runs_extraction_with_defaults(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Forward arguments and print paths returned by the pipeline."""
    calls: list[tuple[Path, Path, str, int]] = []

    def fake_run_extraction(
        input_path: Path,
        output_dir: Path,
        model_name: str,
        *,
        dpi: int,
    ) -> list[Path]:
        """Record the CLI values without running a model."""
        calls.append((input_path, output_dir, model_name, dpi))
        return [Path("output/yolo11/snapshots/example_table_000.png")]

    monkeypatch.setattr(cli, "run_extraction", fake_run_extraction)

    result = cli.main(["--model=yolo11", "--input=data/example.pdf"])

    assert result == 0
    assert calls == [(Path("data/example.pdf"), Path("output"), "yolo11", 300)]
    assert capsys.readouterr().out == (
        "output/yolo11/snapshots/example_table_000.png\n"
    )


def test_main_reports_pipeline_input_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Return a command-line error for an unsupported model."""

    def reject_model(*args: object, **kwargs: object) -> list[Path]:
        """Raise the pipeline's unsupported-model error."""
        raise ValueError("Unsupported model: unknown")

    monkeypatch.setattr(cli, "run_extraction", reject_model)

    with pytest.raises(SystemExit) as error:
        cli.main(["--model=unknown", "--input=data/example.pdf"])

    assert error.value.code == 2
    assert "Unsupported model: unknown" in capsys.readouterr().err


def test_main_rejects_nonpositive_dpi() -> None:
    """Reject a rendering resolution that cannot produce an image."""
    with pytest.raises(SystemExit) as error:
        cli.main(["--model=yolo11", "--input=data/example.pdf", "--dpi=0"])

    assert error.value.code == 2
