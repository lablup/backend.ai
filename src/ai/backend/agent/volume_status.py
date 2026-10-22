from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.agent.config.unified import VolumeConfig
from ai.backend.common.configs.volume_status_check import VolumeStatusCheckConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageVolumeType
from ai.backend.common.exception import InvalidConfigError
from ai.backend.common.storage.probe.registry import VolumeStatusCheck
from ai.backend.common.storage.volume.vfs import VfsVolumeStatusCheck


def create_volume_status_checks(
    volumes: Mapping[StorageVolumeName, VolumeConfig] | None,
) -> Sequence[VolumeStatusCheck]:
    """The status check of every volume that configures one."""
    return [
        _create_volume_status_check(volume_name, volume_config, volume_config.status_check)
        for volume_name, volume_config in (volumes or {}).items()
        if volume_config.status_check is not None
    ]


def _create_volume_status_check(
    volume_name: StorageVolumeName,
    volume_config: VolumeConfig,
    status_check_config: VolumeStatusCheckConfig,
) -> VolumeStatusCheck:
    if volume_config.volume_type == StorageVolumeType("vfs"):
        return VfsVolumeStatusCheck.create(volume_name, volume_config.path, status_check_config)
    raise InvalidConfigError(
        f"Volume status check is not supported for volume type {volume_config.volume_type!r}"
    )
