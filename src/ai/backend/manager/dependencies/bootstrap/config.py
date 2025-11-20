from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.logging.types import LogLevel
from ai.backend.manager.config.bootstrap import BootstrapConfig


@dataclass
class BootstrapConfigInput:
    """Input required for bootstrap configuration loading.

    Contains only the essential parameters needed to load the bootstrap config.
    """

    config_path: Path
    log_level: LogLevel = LogLevel.NOTSET


class BootstrapConfigDependency(
    NonMonitorableDependencyProvider[BootstrapConfigInput, BootstrapConfig]
):
    """Provides BootstrapConfig lifecycle management.

    Loads bootstrap configuration from file with log level overrides.
    """

    @property
    def stage_name(self) -> str:
        return "bootstrap-config"

    @asynccontextmanager
    async def provide(self, setup_input: BootstrapConfigInput) -> AsyncIterator[BootstrapConfig]:
        """Load and provide bootstrap configuration.

        Args:
            setup_input: Input containing config path and log level

        Yields:
            Loaded BootstrapConfig
        """
        config = await BootstrapConfig.load_from_file(
            setup_input.config_path,
            setup_input.log_level,
        )
        yield config
