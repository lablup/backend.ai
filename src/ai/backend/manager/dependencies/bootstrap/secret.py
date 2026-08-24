from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.secret.pool import KeyProviderPool


class KeyProviderPoolDependency(
    NonMonitorableDependencyProvider[ManagerUnifiedConfig, KeyProviderPool]
):
    """Provides the key providers secret columns are written and read through."""

    @property
    @override
    def stage_name(self) -> str:
        return "key-provider-pool"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: ManagerUnifiedConfig) -> AsyncIterator[KeyProviderPool]:
        yield KeyProviderPool.from_config(setup_input.secret_encryption)
