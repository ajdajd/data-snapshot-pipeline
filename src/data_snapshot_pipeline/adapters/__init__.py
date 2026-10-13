"""Create snapshot detector adapters for data snapshot extraction."""

from data_snapshot_pipeline.detection import SnapshotDetector


def create_adapter(model_name: str) -> SnapshotDetector:
    """Create the one snapshot detector selected for a pipeline run.

    Parameters
    ----------
    model_name : str
        Extractor identifier, currently ``"doclayoutyolo"``, ``"tfid"``,
        ``"yolo11"``, or ``"yolo26"``.

    Returns
    -------
    SnapshotDetector
        Selected snapshot detector adapter.

    Raises
    ------
    ValueError
        If the model identifier is not implemented.
    """
    if model_name == "doclayoutyolo":
        from data_snapshot_pipeline.adapters.doclayoutyolo import (
            DocLayoutYOLOAdapter,
        )

        return DocLayoutYOLOAdapter()
    if model_name == "tfid":
        from data_snapshot_pipeline.adapters.tfid import TFIDAdapter

        return TFIDAdapter()
    if model_name == "yolo11":
        from data_snapshot_pipeline.adapters.yolo11 import YOLO11Adapter

        return YOLO11Adapter()
    if model_name == "yolo26":
        from data_snapshot_pipeline.adapters.yolo26 import YOLO26Adapter

        return YOLO26Adapter()
    raise ValueError(f"Unsupported model: {model_name}")
