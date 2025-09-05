from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator
from typing import Optional

from ai.backend.storage.exception import NotImplementedAPI


class AbstractStorage(ABC):
    @abstractmethod
    async def stream_upload(
        self,
        filepath: str,
        data_stream: AsyncIterable[bytes],
        content_type: Optional[str] = None,
    ) -> None:
        raise NotImplementedAPI

    @abstractmethod
    async def stream_download(self, filepath: str) -> AsyncIterator[bytes]:
        raise NotImplementedAPI
        yield b""  # Mark as generator


class StoragePool:
    _storages: dict[str, AbstractStorage]

    def __init__(self, storages: dict[str, AbstractStorage]) -> None:
        self._storages = storages

    def get_storage(self, name: str) -> AbstractStorage:
        return self._storages[name]
