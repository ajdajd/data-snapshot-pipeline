"""Provide the command-line interface for snapshot extraction."""

import argparse
from pathlib import Path

from data_snapshot_pipeline.pipeline import run_extraction


def _positive_int(value: str) -> int:
    """Parse a positive integer command-line value."""
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def main(argv: list[str] | None = None) -> int:
    """Run snapshot extraction from command-line arguments.

    Parameters
    ----------
    argv : list[str] | None, optional
        Arguments to parse, excluding the executable name. Uses ``sys.argv``
        when omitted.

    Returns
    -------
    int
        Zero when extraction completes successfully.

    Raises
    ------
    SystemExit
        If arguments are invalid or extraction cannot start safely.
    """
    parser = argparse.ArgumentParser(
        prog="python -m data_snapshot_pipeline",
        description="Extract snapshots from PDFs.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="One layout model: doclayoutyolo, yolo11, or yolo26.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="A PDF file or directory containing PDFs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output root (default: output).",
    )
    parser.add_argument(
        "--dpi",
        type=_positive_int,
        default=300,
        help="PDF rendering resolution (default: 300).",
    )
    args = parser.parse_args(argv)

    try:
        paths = run_extraction(
            args.input,
            args.output_dir,
            args.model,
            dpi=args.dpi,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    for path in paths:
        print(path)
    return 0
