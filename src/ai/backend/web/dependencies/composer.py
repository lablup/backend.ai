from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import tomli

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.logging.types import LogLevel
from ai.backend.web.config.unified import WebServerUnifiedConfig

from .components import ComponentComposer, ComponentResources
from .infrastructure import InfrastructureComposer, InfrastructureResources


@dataclass
class DependencyInput:
    """
    Input required for complete dependency setup.

    Contains only the essential parameters: config file path and log level.
    """

    config_path: Path
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class DependencyResources:
    """
    Container for all initialized dependency resources.

    Holds all foundational dependencies in the correct initialization order:
    1. Infrastructure stage: redis (valkey session client)
    2. Components stage: manager client, hive router client
    """

    infrastructure: InfrastructureResources
    components: ComponentResources


class WebDependencyComposer(DependencyComposer[DependencyInput, DependencyResources]):
    """
    Composes all web dependencies in the correct order.

    Composes the two-stage dependency initialization:
    1. Infrastructure: redis (valkey session client)
    2. Components: manager client and hive router client
    """

    @property
    def stage_name(self) -> str:
        return "web-dependencies"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DependencyInput,
    ) -> AsyncIterator[DependencyResources]:
        """
        Compose all dependencies in order using the provided stack.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Dependency input containing config path and log level

        Yields:
            DependencyResources containing all initialized resources
        """
        # Load config
        raw_cfg = tomli.loads(setup_input.config_path.read_text(encoding="utf-8"))
        config = WebServerUnifiedConfig.model_validate(raw_cfg)

        # Stage 1: Infrastructure (redis)
        infra_composer = InfrastructureComposer()
        infrastructure = await stack.enter_composer(infra_composer, config)

        # Stage 2: Components (manager client + hive router client)
        components_composer = ComponentComposer()
        components = await stack.enter_composer(components_composer, config)

        # Yield all resources
        yield DependencyResources(
            infrastructure=infrastructure,
            components=components,
        )
