from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from ai.backend.common.types import HostPortPair


class AbstractSentinelMonitor(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_master(self) -> HostPortPair:
        """Return the known master address, querying Sentinel when none is known yet."""
        raise NotImplementedError

    @abstractmethod
    def watch_master(self) -> AsyncGenerator[HostPortPair]:
        """Yield the current master address, then each new one. A slow consumer gets only the latest."""
        raise NotImplementedError

    @abstractmethod
    async def check_master(self, address: HostPortPair) -> HostPortPair:
        """Return the known master if it differs from `address`, otherwise the result of a Sentinel query."""
        raise NotImplementedError
