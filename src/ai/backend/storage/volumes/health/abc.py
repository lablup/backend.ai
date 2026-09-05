from __future__ import annotations

from abc import ABCMeta, abstractmethod

from .types import BackendProbeResult, MountProbeResult


class AbstractMountProber(metaclass=ABCMeta):
    """Answers whether one volume's mount is alive and serving the declared storage."""

    def capture_baseline(self) -> None:
        """
        Records what later probes compare against, once at startup. Blocking, like
        `probe()`. A prober that compares against nothing leaves this empty.
        """

    @abstractmethod
    def probe(self) -> MountProbeResult:
        """
        Blocking on purpose: the probe task submits this to an executor of its own, so a
        dead network mount surfaces as a timeout instead of stalling the event loop.
        """
        raise NotImplementedError


class AbstractBackendProber(metaclass=ABCMeta):
    """Answers whether one volume's backend appliance is reachable from this proxy."""

    @abstractmethod
    async def probe(self) -> BackendProbeResult:
        raise NotImplementedError
