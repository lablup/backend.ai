from __future__ import annotations

import enum
from typing import Self

from ai.backend.common.bgtask.types import BgtaskNameBase


class ManagerBgtaskName(enum.StrEnum, BgtaskNameBase):
    """Background task names for manager component."""

    RESCAN_IMAGES = "rescan_images"
    PURGE_IMAGES = "purge_images"
    RESCAN_GPU_ALLOC_MAPS = "rescan_gpu_alloc_maps"
    CONVERT_SESSION_TO_IMAGE = "convert_session_to_image"
    DRY_RUN_MODEL_SERVICE = "dry_run_model_service"

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Create instance from string value."""
        return cls(value)
