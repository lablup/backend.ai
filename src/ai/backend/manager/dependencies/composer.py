from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.logging.types import LogLevel

from .bootstrap import BootstrapComposer, BootstrapInput
from .infrastructure import (
    InfrastructureComposer,
    InfrastructureInput,
    InfrastructureResources,
)


@dataclass
class DependencyInput:
    """Input required for complete dependency setup.

    Contains only the essential parameters: config file path and log level.
    """

    config_path: Path
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class DependencyResources:
    """Container for all initialized dependency resources.

    Holds all foundational dependencies in the correct initialization order:
    1. Bootstrap stage: etcd
    2. Infrastructure stage: valkey clients, database
    """

    infrastructure: InfrastructureResources


class ManagerDependencyComposer(DependencyComposer[DependencyInput, DependencyResources]):
    """Composes all manager dependencies in the correct order.

    Composes the two-stage dependency initialization:
    1. Bootstrap: etcd and config provider
    2. Infrastructure: valkey clients and database
    """

    @property
    def stage_name(self) -> str:
        return "manager-dependencies"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DependencyInput,
    ) -> AsyncIterator[DependencyResources]:
        """Compose all dependencies in order using the provided stack.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Dependency input containing config path and log level

        Yields:
            DependencyResources containing all initialized resources
        """
        # Stage 1: Bootstrap (etcd + config provider)
        bootstrap_composer = BootstrapComposer()
        bootstrap_input = BootstrapInput(
            config_path=setup_input.config_path,
            log_level=setup_input.log_level,
        )
        bootstrap = await stack.enter_composer(
            bootstrap_composer,
            bootstrap_input,
        )

        # Stage 2: Infrastructure (valkey + database)
        infra_composer = InfrastructureComposer()
        infra_input = InfrastructureInput(
            config=bootstrap.config_provider.config,
            etcd=bootstrap.etcd,
        )
        infrastructure = await stack.enter_composer(
            infra_composer,
            infra_input,
        )

        # Yield all resources
        yield DependencyResources(infrastructure=infrastructure)
