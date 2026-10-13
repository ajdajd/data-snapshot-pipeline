"""Run snapshot extraction with one explicitly selected model."""

from pathlib import Path

from data_snapshot_pipeline.adapters import create_adapter
from data_snapshot_pipeline.extraction import extract_snapshots
from data_snapshot_pipeline.inputs import discover_pdfs
from data_snapshot_pipeline.metadata_extraction import extract_metadata_files


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
        Available paths beneath ``output_dir/model_name/snapshots``.

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


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    model_name: str,
    *,
    dpi: int = 300,
    force: bool = False,
    with_metadata: bool = False,
) -> list[Path]:
    """Run layout extraction and optionally extract semantic metadata.

    Parameters
    ----------
    input_path : str | Path
        One PDF file or a directory searched recursively for PDFs.
    output_dir : str | Path
        Root output directory.
    model_name : str
        Identifier of the single layout model used for this run.
    dpi : int, optional
        PyMuPDF rendering resolution in dots per inch.
    force : bool, optional
        Replace outputs belonging to each source PDF.
    with_metadata : bool, optional
        Extract Schema v1.4 metadata for the available snapshots.

    Returns
    -------
    list[Path]
        Available snapshot paths followed by metadata paths, when requested.

    Raises
    ------
    RuntimeError
        If requested metadata extraction or validation fails.
    ValueError
        If the model identifier or input PDF set is invalid.
    """
    normalized_name = model_name.strip().lower()
    snapshot_paths = run_extraction(
        input_path,
        output_dir,
        normalized_name,
        dpi=dpi,
        force=force,
    )
    if not with_metadata:
        return snapshot_paths

    source_stems = [path.stem for path in discover_pdfs(input_path)]
    metadata_paths = extract_metadata_files(
        snapshot_paths,
        Path(output_dir) / normalized_name / "metadata",
        force=force,
        source_stems=source_stems,
    )
    return [*snapshot_paths, *metadata_paths]
