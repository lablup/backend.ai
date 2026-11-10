from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.storage.client.manager import ManagerHTTPClientPool
from ai.backend.storage.config.unified import (
    LegacyReservoirConfig,
    ReservoirConfig,
    StorageProxyUnifiedConfig,
)


class ManagerClientPoolProvider(
    NonMonitorableDependencyProvider[StorageProxyUnifiedConfig, ManagerHTTPClientPool]
):
    """Provider for the HTTP client pool talking to the reservoir manager registries."""

    @property
    @override
    def stage_name(self) -> str:
        return "manager-client-pool"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: StorageProxyUnifiedConfig
    ) -> AsyncIterator[ManagerHTTPClientPool]:
        registry_configs: dict[str, ReservoirConfig] = {
            name: registry.reservoir
            for name, registry in setup_input.artifact_registries.items()
            if registry.registry_type == ArtifactRegistryType.RESERVOIR
            and registry.reservoir is not None
        }
        for legacy_registry in setup_input.registries:
            if isinstance(legacy_registry.config, LegacyReservoirConfig):
                registry_configs[legacy_registry.name] = legacy_registry.config

        pool = ManagerHTTPClientPool(registry_configs, setup_input.reservoir_client)
        try:
            yield pool
        finally:
            await pool.cleanup()
