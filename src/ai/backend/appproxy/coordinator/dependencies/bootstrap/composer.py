from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack

from ...config import ServerConfig
from .config import ConfigInput, ConfigProvider


@dataclass
class BootstrapInput:
    """Input for bootstrap layer."""

    config_path: Path | None


@dataclass
class BootstrapResources:
    """Bootstrap resources for app proxy coordinator."""

    config: ServerConfig


class BootstrapComposer(DependencyComposer[BootstrapInput, BootstrapResources]):
    """Composer for bootstrap layer dependencies."""

    @property
    def stage_name(self) -> str:
        return "bootstrap"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: BootstrapInput,
    ) -> AsyncIterator[BootstrapResources]:
        """Compose bootstrap dependencies.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Bootstrap input containing config path

        Yields:
            BootstrapResources containing loaded config
        """
        # Load configuration
        config = await stack.enter_dependency(
            ConfigProvider(),
            ConfigInput(config_path=setup_input.config_path),
        )

        yield BootstrapResources(config=config)
