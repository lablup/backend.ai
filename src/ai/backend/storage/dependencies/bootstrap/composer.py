from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

from .config import ConfigProvider, ConfigProviderInput


@dataclass
class BootstrapInput:
    """Input required for bootstrap stage."""

    config_path: Path


@dataclass
class BootstrapResources:
    """Container for bootstrap stage resources."""

    config: StorageProxyUnifiedConfig


class BootstrapComposer(DependencyComposer[BootstrapInput, BootstrapResources]):
    """Composes bootstrap dependencies."""

    @property
    def stage_name(self) -> str:
        return "bootstrap"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: BootstrapInput,
    ) -> AsyncIterator[BootstrapResources]:
        """Compose bootstrap dependencies."""
        # Load config
        config_provider = ConfigProvider()
        config = await stack.enter_dependency(
            config_provider,
            ConfigProviderInput(config_path=setup_input.config_path),
        )

        yield BootstrapResources(config=config)
