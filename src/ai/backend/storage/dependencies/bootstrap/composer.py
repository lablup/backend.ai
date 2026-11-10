from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.logging.types import LogLevel
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

from .config import ConfigProvider, ConfigProviderInput
from .metrics import MetricRegistryProvider


@dataclass
class BootstrapInput:
    """Input required for bootstrap stage."""

    config_path: Path | None
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class BootstrapResources:
    """Container for bootstrap stage resources."""

    config: StorageProxyUnifiedConfig
    metric_registry: CommonMetricRegistry


class BootstrapComposer(DependencyComposer[BootstrapInput, BootstrapResources]):
    """Composes bootstrap dependencies."""

    @property
    @override
    def stage_name(self) -> str:
        return "bootstrap"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: BootstrapInput,
    ) -> AsyncIterator[BootstrapResources]:
        """Compose bootstrap dependencies."""
        config = await stack.enter_dependency(
            ConfigProvider(),
            ConfigProviderInput(
                config_path=setup_input.config_path,
                log_level=setup_input.log_level,
            ),
        )
        metric_registry = await stack.enter_dependency(MetricRegistryProvider(), None)

        yield BootstrapResources(config=config, metric_registry=metric_registry)
