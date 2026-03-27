from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs

from .base import DomainDependency

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
        ValkeyScheduleClient,
    )
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.models.storage import StorageSessionManager
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class RepositoriesInput:
    """Input required for repositories setup."""

    db: ExtendedAsyncSAEngine
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    valkey_stat: ValkeyStatClient
    valkey_live: ValkeyLiveClient
    valkey_schedule: ValkeyScheduleClient
    valkey_image: ValkeyImageClient


class RepositoriesDependency(DomainDependency[RepositoriesInput, Repositories]):
    """Provides Repositories lifecycle management.

    Repositories is a composite dataclass that holds all repository instances
    used across the manager. It requires database, storage, config, and
    valkey client dependencies.
    """

    @property
    def stage_name(self) -> str:
        return "repositories"

    @asynccontextmanager
    async def provide(self, setup_input: RepositoriesInput) -> AsyncIterator[Repositories]:
        """Initialize and provide Repositories.

        Args:
            setup_input: Input containing db, storage_manager, config_provider,
                         and valkey client references.

        Yields:
            Initialized Repositories instance.
        """
        repositories = Repositories.create(
            args=RepositoryArgs(
                db=setup_input.db,
                storage_manager=setup_input.storage_manager,
                config_provider=setup_input.config_provider,
                valkey_stat_client=setup_input.valkey_stat,
                valkey_live_client=setup_input.valkey_live,
                valkey_schedule_client=setup_input.valkey_schedule,
                valkey_image_client=setup_input.valkey_image,
            )
        )
        yield repositories
