from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

import aiohttp

from ai.backend.appproxy.coordinator.dependencies.components.worker_client_pool import (
    WorkerClientPoolProvider,
)
from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.dependencies import DependencyComposer, DependencyStack


@dataclass(frozen=True)
class ComponentsInput:
    worker_client_timeout: aiohttp.ClientTimeout


@dataclass(frozen=True)
class ComponentsResources:
    worker_client_pool: ClientPool


class ComponentsComposer(DependencyComposer[ComponentsInput, ComponentsResources]):
    """Composes the clients the coordinator sends ingresses through."""

    @property
    @override
    def stage_name(self) -> str:
        return "components"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: ComponentsInput,
    ) -> AsyncIterator[ComponentsResources]:
        worker_client_pool = await stack.enter_dependency(
            WorkerClientPoolProvider(), setup_input.worker_client_timeout
        )
        yield ComponentsResources(worker_client_pool=worker_client_pool)
