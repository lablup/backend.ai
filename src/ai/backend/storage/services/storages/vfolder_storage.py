from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.artifact_storage import AbstractStoragePool
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.common.types import VFolderID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.storages.vfolder_storage import VFolderStorage

if TYPE_CHECKING:
    from ai.backend.storage.volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class VFolderStorageSetupResult:
    """Result of VFolderStorageService.setup_for_import() for import operations."""

    storage_step_mappings: dict[ArtifactStorageImportStep, str]
    cleanup_callback: Callable[[], None]


class VFolderStorageService:
    """
    Service class for VFolder storage operations.
    Handles dynamic creation and lifecycle management of VFolderStorage instances.
    """

    _volume_pool: VolumePool
    _storage_pool: AbstractStoragePool

    def __init__(
        self,
        volume_pool: VolumePool,
        storage_pool: AbstractStoragePool,
    ) -> None:
        self._volume_pool = volume_pool
        self._storage_pool = storage_pool

    async def setup(
        self,
        vfid: VFolderID,
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
    ) -> VFolderStorageSetupResult:
        """Setup VFolderStorage for import operations.

        Creates a temporary VFolderStorage, registers it to the storage pool,
        and returns updated storage_step_mappings along with a cleanup callback.

        Args:
            vfid: VFolder ID to create storage for
            storage_step_mappings: Original storage step mappings

        Returns:
            VFolderStorageSetupResult with updated mappings and cleanup callback
        """
        request_id = current_request_id()
        volume_names = set(storage_step_mappings.values())
        if len(volume_names) != 1:
            log.warning(f"Multiple volume names in storage_step_mappings with vfid: {volume_names}")
        volume_name = next(iter(volume_names))

        async with self._volume_pool.get_volume_by_name(volume_name) as volume:
            vfolder_storage_name = f"vfolder_storage_{request_id}"
            vfolder_storage = VFolderStorage(
                name=vfolder_storage_name,
                volume=volume,
                vfid=vfid,
            )
            self._storage_pool.add_storage(vfolder_storage_name, vfolder_storage)

            log.info(
                f"Created VFolderStorage: name={vfolder_storage_name}, vfid={vfid}, "
                f"volume={volume_name}"
            )

        updated_mappings = dict.fromkeys(storage_step_mappings.keys(), vfolder_storage_name)

        def _cleanup() -> None:
            self._storage_pool.remove_storage(vfolder_storage_name)
            log.info(f"Removed VFolderStorage: name={vfolder_storage_name}")

        return VFolderStorageSetupResult(
            storage_step_mappings=updated_mappings,
            cleanup_callback=_cleanup,
        )
