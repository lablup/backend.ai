from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.storage.config.loaders import load_local_config
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig


@dataclass
class ConfigProviderInput:
    """Input for config provider."""

    config_path: Path


class ConfigProvider(
    NonMonitorableDependencyProvider[ConfigProviderInput, StorageProxyUnifiedConfig]
):
    """Provider for storage proxy configuration."""

    @property
    def stage_name(self) -> str:
        return "config"

    @asynccontextmanager
    async def provide(
        self, setup_input: ConfigProviderInput
    ) -> AsyncIterator[StorageProxyUnifiedConfig]:
        """Load and provide storage proxy configuration."""
        config = load_local_config(setup_input.config_path)
        yield config
