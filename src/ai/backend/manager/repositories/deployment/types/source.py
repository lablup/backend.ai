"""Health check configuration sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ai.backend.common.config import ModelHealthCheck

__all__ = ["HealthCheckSource"]


class HealthCheckSource(ABC):
    """
    Base class for health check configuration sources.
    Sources are loaded in order and merged with later sources taking priority.
    """

    @abstractmethod
    async def load(self) -> Optional[ModelHealthCheck]:
        """Load health check configuration from this source."""
        raise NotImplementedError

    def merge(
        self,
        base: Optional[ModelHealthCheck],
        override_: Optional[ModelHealthCheck],
    ) -> Optional[ModelHealthCheck]:
        """
        Merge two health check configs. Override takes priority over base.
        Fields from override are used if present, otherwise base fields are used.
        """
        if base is None and override_ is None:
            return None
        if base is None:
            return override_
        if override_ is None:
            return base

        base_data = base.model_dump()
        override_data = override_.model_dump(exclude_unset=True)
        base_data.update(override_data)
        return ModelHealthCheck.model_validate(base_data)
