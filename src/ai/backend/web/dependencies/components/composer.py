from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.web.config.unified import WebServerUnifiedConfig

from .hive_router_client import HiveRouterClientInfo, HiveRouterClientProvider
from .manager_client import ManagerClientInfo, ManagerClientProvider


@dataclass
class ComponentResources:
    """
    Resources provided by component dependencies.
    """

    manager_client: ManagerClientInfo
    hive_router_client: HiveRouterClientInfo | None


class ComponentComposer(DependencyComposer[WebServerUnifiedConfig, ComponentResources]):
    """
    Composer for component dependencies.
    """

    @property
    def stage_name(self) -> str:
        return "components"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: WebServerUnifiedConfig,
    ) -> AsyncIterator[ComponentResources]:
        """
        Compose component dependencies.
        """
        manager_client = await stack.enter_dependency(ManagerClientProvider(), setup_input)

        # Only setup hive router client if apollo_router is enabled
        hive_router_client = None
        if setup_input.apollo_router.enabled:
            hive_router_client = await stack.enter_dependency(
                HiveRouterClientProvider(), setup_input
            )

        yield ComponentResources(
            manager_client=manager_client,
            hive_router_client=hive_router_client,
        )
