from __future__ import annotations

from abc import ABCMeta, abstractmethod

from .types import BackendProbeResult


class AbstractBackendProber(metaclass=ABCMeta):
    """Answers whether one volume's backend appliance is reachable from this proxy."""

    @abstractmethod
    async def probe(self) -> BackendProbeResult:
        raise NotImplementedError
