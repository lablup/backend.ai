"""Runtime profile source for health check configuration."""

from __future__ import annotations

from typing import Optional, override

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.types import MODEL_SERVICE_RUNTIME_PROFILES, RuntimeVariant

from ..types.health_check_source import HealthCheckSource

__all__ = ["RuntimeProfileSource"]


class RuntimeProfileSource(HealthCheckSource):
    """Load health check config from predefined runtime profiles."""

    def __init__(self, runtime_variant: RuntimeVariant) -> None:
        self._runtime_variant = runtime_variant

    @override
    async def load(self) -> Optional[ModelHealthCheck]:
        profile = MODEL_SERVICE_RUNTIME_PROFILES.get(self._runtime_variant)
        if profile and profile.health_check_endpoint:
            return ModelHealthCheck(path=profile.health_check_endpoint)
        return None
