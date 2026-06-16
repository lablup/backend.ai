from dataclasses import dataclass
from typing import Self

from ai.backend.manager.clients.valkey_client.valkey_cache import ValkeyCache
from ai.backend.manager.repositories.app_config_fragment.admin_repository import (
    AppConfigFragmentAdminRepository,
)
from ai.backend.manager.repositories.app_config_fragment.cache_source import (
    AppConfigFragmentCacheSource,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class AppConfigFragmentRepositories:
    repository: AppConfigFragmentRepository
    admin_repository: AppConfigFragmentAdminRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        # The merged-view read path is fronted by a Valkey cache; the
        # repository falls through to the DB transparently if the
        # cache layer fails.
        valkey_cache = ValkeyCache(args.valkey_stat_client._client)
        cache_source = AppConfigFragmentCacheSource(valkey_cache)
        return cls(
            repository=AppConfigFragmentRepository(
                args.db, args.ops_provider, cache_source=cache_source
            ),
            admin_repository=AppConfigFragmentAdminRepository(
                args.db, args.ops_provider, cache_source=cache_source
            ),
        )
