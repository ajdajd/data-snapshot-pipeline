"""Run snapshot extraction with one explicitly selected model."""

from pathlib import Path

from data_snapshot_pipeline.adapters import create_adapter
from data_snapshot_pipeline.extraction import extract_snapshots


def run_extraction(
    input_path: str | Path,
    output_dir: str | Path,
    model_name: str,
    *,
    dpi: int = 300,
    force: bool = False,
) -> list[Path]:
    """Extract snapshots beneath a directory named for the selected model.

    Parameters
    ----------
    input_path : str | Path
        One PDF file or a directory searched recursively for PDFs.
    output_dir : str | Path
        Root output directory.
    model_name : str
        Identifier of the single model used for this run.
    dpi : int, optional
        PyMuPDF rendering resolution in dots per inch.
    force : bool, optional
        Delete existing snapshots for each source PDF before extracting it.

    Returns
    -------
    list[Path]
        Paths written beneath ``output_dir/model_name/snapshots``.

    Raises
    ------
    ValueError
        If the model identifier is not implemented.
    """
    normalized_name = model_name.strip().lower()
    adapter = create_adapter(normalized_name)
    return extract_snapshots(
        input_path,
        Path(output_dir) / normalized_name,
        adapter,
        dpi=dpi,
        force=force,
    )
