from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Final

from pydantic import Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import StorageBackendType
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

DEFAULT_VOLUME_CHECK_INTERVAL: Final[float] = 60.0


class VolumeConfig(BaseConfigSchema):
    """What every service holding a volume declares about it; a volume type adds its own fields."""

    volume_type: Annotated[
        StorageBackendType,
        Field(),
        BackendAIConfigMeta(
            description="The storage backend type of this volume, such as 'vfs'.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local="vfs", prod="vfs"),
        ),
    ]
    check_interval: Annotated[
        float,
        Field(default=DEFAULT_VOLUME_CHECK_INTERVAL, gt=0),
        BackendAIConfigMeta(
            description="Seconds between two status checks of this volume.",
            added_version=NEXT_RELEASE_VERSION,
            example=ConfigExample(local=60, prod=60),
        ),
    ]


class VolumeConfigs(BaseConfigSchema):
    volumes: Annotated[
        Mapping[StorageVolumeID, VolumeConfig],
        Field(default_factory=dict),
        BackendAIConfigMeta(
            description="The volumes this service holds, keyed by volume id.",
            added_version=NEXT_RELEASE_VERSION,
            composite=CompositeType.DICT,
        ),
    ]
