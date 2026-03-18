from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.types import DistributedLockFactory

from .distributed_lock import DistributedLockFactoryDependency, DistributedLockInput
from .notification import NotificationCenterDependency
from .repositories import RepositoriesDependency, RepositoriesInput
from .services import ServicesContextDependency, ServicesInput

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
        ValkeyScheduleClient,
    )
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.models.storage import StorageSessionManager
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class DomainInput:
    """Input required for domain setup.

    Contains infrastructure and component resources from earlier stages.
    """

    config_provider: ManagerConfigProvider
    db: ExtendedAsyncSAEngine
    etcd: AsyncEtcd
    storage_manager: StorageSessionManager
    valkey_stat: ValkeyStatClient
    valkey_live: ValkeyLiveClient
    valkey_schedule: ValkeyScheduleClient
    valkey_image: ValkeyImageClient


@dataclass
class DomainResources:
    """Container for all domain resources."""

    notification_center: NotificationCenter
    distributed_lock_factory: DistributedLockFactory
    repositories: Repositories
    services_ctx: ServicesContext


class DomainComposer(DependencyComposer[DomainInput, DomainResources]):
    """Composes all domain dependencies.

    Composes repositories and domain objects at Layer 0+3:
    1. Notification center: HTTP client pool for notifications (no deps)
    2. Distributed lock factory: Lock backend based on config
    3. Repositories: All repository instances
    4. Services context: Service-layer objects for the API layer
    """

    @property
    def stage_name(self) -> str:
        return "domain"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: DomainInput,
    ) -> AsyncIterator[DomainResources]:
        """Compose domain dependencies in order.

        Args:
            stack: The dependency stack to use for composition.
            setup_input: Domain input containing infrastructure and component resources.

        Yields:
            DomainResources containing all domain dependencies.
        """
        # 1. Notification center (no dependencies)
        notification_center_dep = NotificationCenterDependency()
        notification_center = await stack.enter_dependency(notification_center_dep, None)

        # 2. Distributed lock factory (depends on config, db, etcd)
        distributed_lock_dep = DistributedLockFactoryDependency()
        distributed_lock_input = DistributedLockInput(
            config_provider=setup_input.config_provider,
            db=setup_input.db,
            etcd=setup_input.etcd,
        )
        distributed_lock_factory = await stack.enter_dependency(
            distributed_lock_dep, distributed_lock_input
        )

        # 3. Repositories (depends on db, storage_manager, config, valkey clients)
        repositories_dep = RepositoriesDependency()
        repositories_input = RepositoriesInput(
            db=setup_input.db,
            storage_manager=setup_input.storage_manager,
            config_provider=setup_input.config_provider,
            valkey_stat=setup_input.valkey_stat,
            valkey_live=setup_input.valkey_live,
            valkey_schedule=setup_input.valkey_schedule,
            valkey_image=setup_input.valkey_image,
        )
        repositories = await stack.enter_dependency(repositories_dep, repositories_input)

        # 4. Services context (depends on db)
        services_dep = ServicesContextDependency()
        services_input = ServicesInput(db=setup_input.db)
        services_ctx = await stack.enter_dependency(services_dep, services_input)

        yield DomainResources(
            notification_center=notification_center,
            distributed_lock_factory=distributed_lock_factory,
            repositories=repositories,
            services_ctx=services_ctx,
        )
