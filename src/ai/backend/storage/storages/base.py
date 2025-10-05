import logging
from abc import ABC, abstractmethod

from ai.backend.common.types import StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import NotImplementedAPI

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractStorage(ABC):
    @abstractmethod
    async def stream_upload(
        self,
        filepath: str,
        data_stream: StreamReader,
    ) -> None:
        raise NotImplementedAPI

    @abstractmethod
    async def stream_download(self, filepath: str) -> StreamReader:
        raise NotImplementedAPI
