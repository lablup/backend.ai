from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.common.types import StreamReader


class AbstractStorage(ABC):
    @abstractmethod
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stream_download(self, filepath: str) -> StreamReader:
        raise NotImplementedError

    @abstractmethod
    async def delete_file(self, filepath: str) -> None:
        raise NotImplementedError

    @abstractmethod
    # TODO: Remove Any and define a proper return type
    async def get_file_info(self, filepath: str) -> Any:
        raise NotImplementedError


class StoragePoolProtocol(Protocol):
    """Protocol for StoragePool interface"""

    def get_storage(self, name: str) -> AbstractStorage:
        """Get storage by name"""
        ...

    def add_storage(self, name: str, storage: AbstractStorage) -> None:
        """Add a storage to the pool"""
        ...

    def remove_storage(self, name: str) -> None:
        """Remove a storage from the pool"""
        ...

    def list_storages(self) -> list[str]:
        """List all storage names in the pool"""
        ...

    def has_storage(self, name: str) -> bool:
        """Check if storage exists in the pool"""
        ...


@dataclass
class ImportStepContext:
    """Context shared across import steps"""

    model: ModelTarget
    registry_name: str
    storage_pool: StoragePoolProtocol
    storage_step_mappings: dict[ArtifactStorageImportStep, str]
    step_metadata: dict[str, Any]  # For passing data between steps
