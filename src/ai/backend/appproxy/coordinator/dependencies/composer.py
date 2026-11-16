from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final, override

import aiohttp

from ai.backend.common.dependencies import DependencyComposer, DependencyStack

from .bootstrap import BootstrapComposer, BootstrapInput, BootstrapResources
from .components.composer import ComponentsComposer, ComponentsInput, ComponentsResources
from .infrastructure import InfrastructureComposer, InfrastructureResources
from .system.composer import SystemComposer, SystemInput, SystemResources

_WORKER_CLIENT_TIMEOUT: Final[aiohttp.ClientTimeout] = aiohttp.ClientTimeout(
    total=30.0, connect=10.0
)
_MAX_CONCURRENT_TRAEFIK_ETCD_CALLS: Final[int] = 16


@dataclass
class DependencyInput:
    """Input required for complete dependency setup."""

    config_path: Path | None = None


@dataclass
class DependencyResources:
    """All dependency resources for app proxy coordinator."""

    bootstrap: BootstrapResources
    infrastructure: InfrastructureResources
    system: SystemResources
    components: ComponentsResources


class CoordinatorDependencyComposer(DependencyComposer[DependencyInput, DependencyResources]):
    """Main composer for all app proxy coordinator dependencies."""

    @property
    @override
    def stage_name(self) -> str:
        return "coordinator"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DependencyInput,
    ) -> AsyncIterator[DependencyResources]:
        """Compose all app proxy coordinator dependencies."""
        # Stage 1: Bootstrap (config)
        bootstrap = await stack.enter_composer(
            BootstrapComposer(),
            BootstrapInput(config_path=setup_input.config_path),
        )

        # Stage 2: Infrastructure (database, redis, etcd)
        infrastructure = await stack.enter_composer(
            InfrastructureComposer(),
            bootstrap.config,
        )

        # Stage 3: System (service discovery)
        system = await stack.enter_composer(
            SystemComposer(),
            SystemInput(
                config=bootstrap.config,
                sentinel_monitors=infrastructure.sentinel_monitors,
            ),
        )

        # Stage 4: Components (worker client pool, Traefik worker client)
        components = await stack.enter_composer(
            ComponentsComposer(),
            ComponentsInput(
                config=bootstrap.config,
                worker_client_timeout=_WORKER_CLIENT_TIMEOUT,
                traefik_etcd=infrastructure.traefik_etcd,
                worker_service_discovery=system.worker_service_discovery,
                max_concurrent_traefik_etcd_calls=_MAX_CONCURRENT_TRAEFIK_ETCD_CALLS,
            ),
        )

        yield DependencyResources(
            bootstrap=bootstrap,
            infrastructure=infrastructure,
            system=system,
            components=components,
        )
