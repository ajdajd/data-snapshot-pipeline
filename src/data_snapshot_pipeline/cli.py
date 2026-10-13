"""Provide the command-line interface for snapshot and metadata extraction."""

import argparse
import sys
from pathlib import Path

from data_snapshot_pipeline.pipeline import run_pipeline


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
        description="Extract snapshots and optional metadata from PDFs.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="One layout model: doclayoutyolo, tfid, yolo11, or yolo26.",
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
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Replace existing outputs for each input PDF.",
    )
    parser.add_argument(
        "--with-metadata",
        action="store_true",
        help="Extract Schema v1.4 metadata for each snapshot.",
    )
    args = parser.parse_args(argv)

    try:
        paths = run_pipeline(
            args.input,
            args.output_dir,
            args.model,
            dpi=args.dpi,
            force=args.force,
            with_metadata=args.with_metadata,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    for path in paths:
        print(path)
    return 0
