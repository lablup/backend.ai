from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.logging.types import LogLevel

from .bootstrap import BootstrapComposer, BootstrapInput, BootstrapResources
from .infrastructure.composer import (
    InfrastructureComposer,
    InfrastructureComposerInput,
    InfrastructureResources,
)
from .messaging.composer import (
    MessagingComposer,
    MessagingComposerInput,
    MessagingResources,
)
from .plugins.base import PluginsInput
from .plugins.composer import PluginsComposer, PluginsResources
from .storage.composer import StorageComposer, StorageComposerInput, StorageResources
from .system.composer import SystemComposer, SystemComposerInput, SystemResources


@dataclass
class DependencyInput:
    """Input required for complete dependency setup."""

    config_path: Path | None
    pidx: int = 0
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class DependencyResources:
    """All dependency resources for storage proxy.

    Holds all dependencies in the correct initialization order:
    0. Bootstrap stage: config, metric registry
    1. Infrastructure stage: etcd, redis config, valkey clients
    2. Plugins stage: storage backend plugin context, volume backend registry
    3. Messaging stage: message queue, event producer, event dispatcher
    4. Storage stage: storage pool, volume pool, bgtask manager, watcher,
       volume stats, manager client pool
    5. System stage: health probe, service discovery
    """

    bootstrap: BootstrapResources
    infrastructure: InfrastructureResources
    plugins: PluginsResources
    messaging: MessagingResources
    storage: StorageResources
    system: SystemResources


class StorageDependencyComposer(DependencyComposer[DependencyInput, DependencyResources]):
    """Main composer for all storage proxy dependencies."""

    @property
    @override
    def stage_name(self) -> str:
        return "storage-proxy"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DependencyInput,
    ) -> AsyncIterator[DependencyResources]:
        """Compose all storage proxy dependencies."""
        bootstrap = await stack.enter_composer(
            BootstrapComposer(),
            BootstrapInput(
                config_path=setup_input.config_path,
                log_level=setup_input.log_level,
            ),
        )
        local_config = bootstrap.config

        infrastructure = await stack.enter_composer(
            InfrastructureComposer(),
            InfrastructureComposerInput(local_config=local_config, pidx=setup_input.pidx),
        )

        plugins = await stack.enter_composer(
            PluginsComposer(),
            PluginsInput(etcd=infrastructure.etcd, local_config=local_config.model_dump()),
        )

        messaging = await stack.enter_composer(
            MessagingComposer(),
            MessagingComposerInput(
                local_config=local_config,
                redis_config=infrastructure.redis_config,
                metric_registry=bootstrap.metric_registry,
            ),
        )

        storage = await stack.enter_composer(
            StorageComposer(),
            StorageComposerInput(
                local_config=local_config,
                pidx=setup_input.pidx,
                etcd=infrastructure.etcd,
                valkey=infrastructure.valkey,
                event_dispatcher=messaging.event_dispatcher,
                event_producer=messaging.event_producer,
                backends=plugins.backends,
            ),
        )

        system = await stack.enter_composer(
            SystemComposer(),
            SystemComposerInput(
                local_config=local_config,
                etcd=infrastructure.etcd,
                redis_config=infrastructure.redis_config,
                valkey=infrastructure.valkey,
                event_producer=messaging.event_producer,
            ),
        )

        yield DependencyResources(
            bootstrap=bootstrap,
            infrastructure=infrastructure,
            plugins=plugins,
            messaging=messaging,
            storage=storage,
            system=system,
        )
