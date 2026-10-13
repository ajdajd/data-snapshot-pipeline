"""Write validated metadata JSON for extracted snapshot images."""

from pathlib import Path
from typing import Iterable

from data_snapshot_pipeline.metadata_extraction.extraction import extract_metadata


def extract_metadata_files(
    snapshot_paths: Iterable[str | Path],
    output_dir: str | Path,
    *,
    force: bool = False,
    source_stems: Iterable[str] = (),
) -> list[Path]:
    """Extract and save metadata for snapshot images.

    Parameters
    ----------
    snapshot_paths : Iterable[str | Path]
        Snapshot images to process.
    output_dir : str | Path
        Directory for one JSON file per snapshot.
    force : bool, optional
        Replace matching metadata and remove stale metadata for the sources.
    source_stems : Iterable[str], optional
        Source PDF stems used to identify stale metadata when forcing a run.

    Returns
    -------
    list[Path]
        Available metadata JSON paths in snapshot order.

    Raises
    ------
    RuntimeError
        If metadata extraction or validation fails for a snapshot.
    """
    metadata_dir = Path(output_dir)
    output_paths: list[Path] = []
    pending: list[tuple[Path, str]] = []

    for snapshot_path_value in snapshot_paths:
        snapshot_path = Path(snapshot_path_value)
        metadata_path = metadata_dir / f"{snapshot_path.stem}.json"
        output_paths.append(metadata_path)
        if metadata_path.exists() and not force:
            print(
                f"Skipping {snapshot_path}: existing metadata found at "
                f"{metadata_path} (use --force to replace)."
            )
            continue

        result = extract_metadata(snapshot_path)
        if result.metadata is None:
            detail = result.error or "unknown extraction error"
            raise RuntimeError(
                f"Metadata extraction failed for {snapshot_path}: {detail}"
            )
        pending.append(
            (metadata_path, result.metadata.model_dump_json(indent=2) + "\n")
        )

    if pending:
        metadata_dir.mkdir(parents=True, exist_ok=True)
    for metadata_path, serialized in pending:
        temporary_path = metadata_path.with_suffix(".json.tmp")
        temporary_path.write_text(serialized, encoding="utf-8")
        temporary_path.replace(metadata_path)

    if force and metadata_dir.is_dir():
        keep = set(output_paths)
        stale_paths = _existing_metadata_paths(metadata_dir, source_stems) - keep
        for stale_path in sorted(stale_paths):
            stale_path.unlink()

    return output_paths


def _existing_metadata_paths(
    metadata_dir: Path, source_stems: Iterable[str]
) -> set[Path]:
    """Return metadata outputs belonging to selected PDF stems."""
    prefixes = tuple(
        prefix
        for source_stem in source_stems
        for prefix in (f"{source_stem}_figure_", f"{source_stem}_table_")
    )
    if not prefixes:
        return set()
    return {
        path
        for path in metadata_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".json"
        and path.name.startswith(prefixes)
    }
