"""Active handle to a created instance.

A backend returns ComputeInstance objects rather than plain data so that
observation (stats) rides on the object that already holds the backend-native
reference. Lifecycle triggers stay on ComputeBackend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.agent.compute_backend.types import InstanceInfo, InstanceStat


class ComputeInstance(ABC):
    @property
    @abstractmethod
    def info(self) -> InstanceInfo:
        raise NotImplementedError

    @abstractmethod
    async def collect_stats(self) -> InstanceStat:
        raise NotImplementedError
