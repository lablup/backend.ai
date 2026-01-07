from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from uuid import UUID

from ai.backend.common.data.storage.types import ArtifactStorageImportStep, ArtifactStorageType
from ai.backend.common.types import VFolderID
from ai.backend.manager.config.unified import (
    ReservoirConfig,
    ReservoirObjectStorageConfig,
    ReservoirVFSStorageConfig,
)
from ai.backend.manager.errors.storage import (
    UnsupportedStorageTypeError,
    VFolderNotFound,
    VFolderStorageNamespaceNotResolvableError,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
    from ai.backend.manager.repositories.storage_namespace.repository import (
        StorageNamespaceRepository,
    )
    from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
    from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository


@dataclass(frozen=True)
class ImportDestinationInfo:
    """Resolved import destination information."""

    storage_host: str
    storage_step_mappings: dict[ArtifactStorageImportStep, str]
    vfid: VFolderID | None
    storage_type: str | None
    namespace_id: UUID | None


class ArtifactImportDestinationResolver:
    """Resolves import destination based on vfolder_id or reservoir configuration.

    This class encapsulates the logic for determining where artifacts should be
    imported to, supporting both vfolder destinations and configured storage backends.
    """

    _vfolder_repository: VfolderRepository
    _object_storage_repository: ObjectStorageRepository
    _vfs_storage_repository: VFSStorageRepository
    _storage_namespace_repository: StorageNamespaceRepository

    def __init__(
        self,
        vfolder_repository: VfolderRepository,
        object_storage_repository: ObjectStorageRepository,
        vfs_storage_repository: VFSStorageRepository,
        storage_namespace_repository: StorageNamespaceRepository,
    ) -> None:
        self._vfolder_repository = vfolder_repository
        self._object_storage_repository = object_storage_repository
        self._vfs_storage_repository = vfs_storage_repository
        self._storage_namespace_repository = storage_namespace_repository

    async def resolve(
        self,
        reservoir_config: ReservoirConfig,
        vfolder_id: UUID | None = None,
    ) -> ImportDestinationInfo:
        """Resolve import destination based on vfolder_id or reservoir configuration.

        Args:
            reservoir_config: Reservoir configuration
            vfolder_id: Optional vfolder ID for vfolder-based import

        Returns:
            ImportDestinationInfo with resolved destination details
        """
        if vfolder_id:
            return await self._resolve_vfolder_destination(vfolder_id)
        return await self._resolve_storage_destination(reservoir_config)

    async def _resolve_vfolder_destination(self, vfolder_id: UUID) -> ImportDestinationInfo:
        """Resolve destination for vfolder-based import."""
        vfolder_data = await self._vfolder_repository.get_by_id(vfolder_id)
        if vfolder_data is None:
            raise VFolderNotFound(f"VFolder with id {vfolder_id} not found")

        vfid = VFolderID(vfolder_data.quota_scope_id, vfolder_data.id)
        # vfolder.host format: "{proxy_name}:{volume_name}"
        proxy_name, _, volume_name = vfolder_data.host.partition(":")
        storage_host = proxy_name  # storage proxy client only needs proxy name

        # Override storage_step_mappings to use vfolder's volume for all steps
        storage_step_mappings: dict[ArtifactStorageImportStep, str] = dict.fromkeys(
            [
                ArtifactStorageImportStep.DOWNLOAD,
                ArtifactStorageImportStep.VERIFY,
                ArtifactStorageImportStep.ARCHIVE,
            ],
            volume_name,  # storage step mappings use volume name
        )

        return ImportDestinationInfo(
            storage_host=storage_host,
            storage_step_mappings=storage_step_mappings,
            vfid=vfid,
            storage_type=None,
            namespace_id=None,
        )

    async def _resolve_storage_destination(
        self, reservoir_config: ReservoirConfig
    ) -> ImportDestinationInfo:
        """Resolve destination for configured storage backend."""
        storage_type = reservoir_config.config.storage_type
        reservoir_archive_storage = reservoir_config.archive_storage
        namespace = self.resolve_storage_namespace(reservoir_config)

        storage_host, namespace_id, _ = await self._get_storage_info(
            reservoir_archive_storage, namespace
        )
        storage_step_mappings = reservoir_config.resolve_storage_step_selection()

        return ImportDestinationInfo(
            storage_host=storage_host,
            storage_step_mappings=storage_step_mappings,
            vfid=None,
            storage_type=storage_type,
            namespace_id=namespace_id,
        )

    def resolve_storage_namespace(self, reservoir_config: ReservoirConfig) -> str:
        """Resolve namespace based on storage type.

        Args:
            reservoir_config: Reservoir configuration

        Returns:
            Namespace (bucket name for object storage, subpath for VFS storage)
        """
        match reservoir_config.config.storage_type:
            case ArtifactStorageType.OBJECT_STORAGE.value:
                return cast(ReservoirObjectStorageConfig, reservoir_config.config).bucket_name
            case ArtifactStorageType.VFS_STORAGE.value:
                return cast(ReservoirVFSStorageConfig, reservoir_config.config).subpath
            case ArtifactStorageType.VFOLDER_STORAGE.value:
                # VFolder storage namespace is not resolvable via static configuration.
                # vfolder_id is provided dynamically as an argument to import_artifacts.
                raise VFolderStorageNamespaceNotResolvableError(
                    "VFolder storage namespace must be resolved dynamically via vfolder_id argument"
                )
            case _:
                raise UnsupportedStorageTypeError(
                    f"Unsupported storage type: {reservoir_config.config.storage_type}"
                )

    async def _get_storage_info(
        self, storage_name: str, namespace: str
    ) -> tuple[str, uuid.UUID, str]:
        """Get storage info by trying object_storage first, then vfs_storage as fallback.

        Args:
            storage_name: Name of the storage
            namespace: Bucket name for object storage or subpath for VFS storage

        Returns:
            Tuple of (storage_host, namespace_id, storage_name)
        """
        try:
            object_storage_data = await self._object_storage_repository.get_by_name(storage_name)
            storage_namespace = (
                await self._storage_namespace_repository.get_by_storage_and_namespace(
                    object_storage_data.id, namespace
                )
            )
            return (
                object_storage_data.host,
                storage_namespace.id,
                object_storage_data.name,
            )
        except Exception:
            vfs_storage_data = await self._vfs_storage_repository.get_by_name(storage_name)
            storage_namespace = (
                await self._storage_namespace_repository.get_by_storage_and_namespace(
                    vfs_storage_data.id, namespace
                )
            )
            return vfs_storage_data.host, storage_namespace.id, vfs_storage_data.name
