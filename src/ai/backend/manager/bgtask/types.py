from __future__ import annotations

import enum


class ManagerBgtaskName(enum.StrEnum):
    """Background task names for manager component."""

    RESCAN_IMAGES = "rescan_images"
    PURGE_IMAGES = "purge_images"
    RESCAN_GPU_ALLOC_MAPS = "rescan_gpu_alloc_maps"
    CONVERT_SESSION_TO_IMAGE = "convert_session_to_image"
    DRY_RUN_MODEL_SERVICE = "dry_run_model_service"
