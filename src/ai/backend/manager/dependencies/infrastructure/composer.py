from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .database import DatabaseDependency
from .redis import ValkeyClients, ValkeyDependency


@dataclass
class InfrastructureInput:
    """Input required for infrastructure setup.

    Contains the unified configuration and an already-initialized etcd client
    from the bootstrap stage.
    """

    config: ManagerUnifiedConfig
    etcd: AsyncEtcd


@dataclass
class InfrastructureResources:
    """Container for all initialized infrastructure resources.

    Holds initialized foundational dependencies (etcd, valkey clients, database)
    that are used throughout the server lifecycle or CLI execution.
    """

    etcd: AsyncEtcd
    valkey: ValkeyClients
    db: ExtendedAsyncSAEngine


class InfrastructureComposer(DependencyComposer[InfrastructureInput, InfrastructureResources]):
    """Composes all infrastructure dependencies as a single unit.

    Composes valkey and database dependencies in order.
    Etcd is passed from the bootstrap stage and not managed here.
    """

    @property
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: InfrastructureInput,
    ) -> AsyncIterator[InfrastructureResources]:
        """Compose all infrastructure dependencies.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Infrastructure input containing config and etcd client

        Yields:
            InfrastructureResources containing all initialized resources
        """
        # Initialize dependency providers
        valkey_dep = ValkeyDependency()
        db_dep = DatabaseDependency()

        # Enter dependencies using the stack
        valkey = await stack.enter_dependency(
            valkey_dep,
            setup_input.config,
        )
        db = await stack.enter_dependency(
            db_dep,
            setup_input.config,
        )

        # Yield the infrastructure resources
        yield InfrastructureResources(
            etcd=setup_input.etcd,
            valkey=valkey,
            db=db,
        )
