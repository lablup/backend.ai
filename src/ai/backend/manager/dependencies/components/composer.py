from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .agent_cache import AgentCacheDependency, AgentCacheInput
from .storage import StorageManagerDependency


@dataclass
class ComponentsInput:
    """Input required for components setup.

    Contains configuration and infrastructure resources.
    """

    config: ManagerUnifiedConfig
    db: ExtendedAsyncSAEngine
    etcd: AsyncEtcd


@dataclass
class ComponentsResources:
    """Container for all component resources.

    Holds storage manager and agent cache.
    """

    storage_manager: StorageSessionManager
    agent_cache: AgentRPCCache


class ComponentsComposer(DependencyComposer[ComponentsInput, ComponentsResources]):
    """Composes all component dependencies.

    Composes storage and agent-related components:
    1. Storage manager: Handles storage proxy sessions
    2. Agent cache: Manages agent RPC connections and authentication
    """

    @property
    def stage_name(self) -> str:
        return "components"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: ComponentsInput,
    ) -> AsyncIterator[ComponentsResources]:
        """Compose component dependencies in order.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Components input containing config and infrastructure

        Yields:
            ComponentsResources containing storage manager and agent cache
        """
        # Initialize storage manager
        storage_dep = StorageManagerDependency()
        storage_manager = await stack.enter_dependency(
            storage_dep,
            setup_input.config,
        )

        # Initialize agent cache with manager keypair
        agent_cache_dep = AgentCacheDependency()
        agent_cache_input = AgentCacheInput(
            db=setup_input.db,
            config=setup_input.config,
        )
        agent_cache = await stack.enter_dependency(
            agent_cache_dep,
            agent_cache_input,
        )

        # Yield component resources
        yield ComponentsResources(
            storage_manager=storage_manager,
            agent_cache=agent_cache,
        )
