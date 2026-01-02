from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import NonMonitorableDependencyProvider

from ...config import ServerConfig, load


@dataclass
class ConfigInput:
    """Input for loading configuration."""

    config_path: Path | None


class ConfigProvider(NonMonitorableDependencyProvider[ConfigInput, ServerConfig]):
    """Provider for app proxy coordinator configuration."""

    @property
    def stage_name(self) -> str:
        return "config"

    @asynccontextmanager
    async def provide(self, setup_input: ConfigInput) -> AsyncIterator[ServerConfig]:
        """Load and provide server configuration.

        Args:
            setup_input: Input containing config path

        Yields:
            Loaded ServerConfig
        """
        config = load(setup_input.config_path)
        yield config
