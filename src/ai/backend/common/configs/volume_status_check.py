from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.data.storage.types import StorageBackendType
from ai.backend.common.exception import InvalidConfigError
from ai.backend.common.meta import NEXT_RELEASE_VERSION, BackendAIConfigMeta, ConfigExample


class VolumeStatusCheckConfig(BaseConfigSchema):
    check_interval: Annotated[
        float,
        Field(
            default=60.0,
            gt=0,
            validation_alias=AliasChoices("check-interval", "check_interval"),
            serialization_alias="check-interval",
        ),
        BackendAIConfigMeta(
            description="Seconds between two status checks of a volume.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="60", prod="60"),
        ),
    ]


class VfsVolumeStatusCheckConfig(VolumeStatusCheckConfig):
    marker_filename: Annotated[
        str,
        Field(
            default=".backend.ai-volume-id",
            validation_alias=AliasChoices("marker-filename", "marker_filename"),
            serialization_alias="marker-filename",
        ),
        BackendAIConfigMeta(
            description="The file at a volume's mount root an operator writes the volume id into.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local=".backend.ai-volume-id", prod=".backend.ai-volume-id"),
        ),
    ]


def validate_volume_status_check_config(
    backend: StorageBackendType, config: VolumeStatusCheckConfig
) -> VolumeStatusCheckConfig:
    """Validates a volume status check config against the schema of the volume's backend."""
    if backend != StorageBackendType("vfs"):
        raise InvalidConfigError(f"Volume status check is not supported for backend {backend!r}")
    return VfsVolumeStatusCheckConfig.model_validate(config.model_dump(by_alias=True))
