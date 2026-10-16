"""
Common types for Storage Volume DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.data.storage.types import StorageVolumeUsageField
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "StorageVolumeOrderField",
    "StorageVolumeServiceAttachmentOrderField",
    "StorageVolumeUsageExposureInfo",
    "StorageVolumeUsageExposureInput",
    "StorageVolumeUsageField",
)


class StorageVolumeOrderField(StrEnum):
    """Fields available for ordering storage volumes."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class StorageVolumeServiceAttachmentOrderField(StrEnum):
    """Fields available for ordering the storage volume service attachments."""

    SERVICE_CATALOG_ID = "service_catalog_id"
    STORAGE_VOLUME_ID = "storage_volume_id"
    STATUS_CHECKED_AT = "status_checked_at"
    UPDATED_AT = "updated_at"


class StorageVolumeUsageExposureInfo(BaseResponseModel):
    """Which usage figures a volume shows a user."""

    exposed: list[StorageVolumeUsageField] = Field(
        description="The usage figures the volume shows."
    )


class StorageVolumeUsageExposureInput(BaseRequestModel):
    """Input for which usage figures a volume shows a user."""

    exposed: list[StorageVolumeUsageField] = Field(
        description="The usage figures the volume shows. Replaces the whole set."
    )
