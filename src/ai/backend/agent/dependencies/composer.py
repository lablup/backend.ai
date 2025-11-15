from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.logging.types import LogLevel

from .bootstrap import AgentBootstrapComposer, AgentBootstrapInput
from .infrastructure import (
    AgentInfrastructureComposer,
    AgentInfrastructureInput,
    AgentInfrastructureResources,
)


@dataclass
class AgentDependencyInput:
    """Input required for complete agent dependency setup.

    Contains only the essential parameters: config file path and log level,
    matching server.py's main() function parameters.
    """

    config_path: Path | None = None
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class AgentDependencyResources:
    """Container for all initialized agent dependency resources.

    Holds all foundational dependencies in the correct initialization order:
    1. Infrastructure stage: etcd, valkey clients, docker
    """

    infrastructure: AgentInfrastructureResources


class AgentDependencyComposer(DependencyComposer[AgentDependencyInput, AgentDependencyResources]):
    """Composes all agent dependencies in the correct order.

    Composes the two-stage dependency initialization:
    1. Bootstrap: config loading + etcd initialization
    2. Infrastructure: valkey clients + docker
    """

    @property
    def stage_name(self) -> str:
        return "agent-dependencies"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: AgentDependencyInput,
    ) -> AsyncIterator[AgentDependencyResources]:
        """Compose all dependencies in order using the provided stack.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Dependency input containing config path and log level

        Yields:
            AgentDependencyResources containing all initialized resources
        """
        # Stage 1: Bootstrap (config loading + etcd)
        bootstrap = await stack.enter_composer(
            AgentBootstrapComposer(),
            AgentBootstrapInput(
                config_path=setup_input.config_path,
                log_level=setup_input.log_level,
            ),
        )

        # Stage 2: Infrastructure (valkey + docker)
        infrastructure = await stack.enter_composer(
            AgentInfrastructureComposer(),
            AgentInfrastructureInput(
                config=bootstrap.config,
                etcd=bootstrap.etcd,
                redis_config=bootstrap.redis_config,
            ),
        )

        # Yield all resources
        yield AgentDependencyResources(
            infrastructure=infrastructure,
        )
