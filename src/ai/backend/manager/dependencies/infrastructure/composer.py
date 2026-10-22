from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.sentinel_monitor.dependency import (
    SentinelMonitorDependency,
)
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import (
    SentinelMonitorSet,
)
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .database import DatabaseDependency
from .redis import ValkeyClients, ValkeyDependency, ValkeyInput


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
    sentinel_monitors: SentinelMonitorSet
    valkey: ValkeyClients
    db: ExtendedAsyncSAEngine


class InfrastructureComposer(DependencyComposer[InfrastructureInput, InfrastructureResources]):
    """Composes all infrastructure dependencies as a single unit.

    Composes Sentinel monitor, valkey and database dependencies in order.
    Etcd is passed from the bootstrap stage and not managed here.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    @override
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
        sentinel_monitors = await stack.enter_dependency(
            SentinelMonitorDependency(),
            setup_input.config.redis.to_valkey_profile_target().targets(),
        )
        valkey = await stack.enter_dependency(
            valkey_dep,
            ValkeyInput(config=setup_input.config, sentinel_monitors=sentinel_monitors),
        )
        db = await stack.enter_dependency(
            db_dep,
            setup_input.config,
        )

        # Yield the infrastructure resources
        yield InfrastructureResources(
            etcd=setup_input.etcd,
            sentinel_monitors=sentinel_monitors,
            valkey=valkey,
            db=db,
        )
