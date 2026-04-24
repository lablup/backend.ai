from __future__ import annotations

import uuid

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.db_source import (
    AppConfigPolicyDBSource,
)


class AppConfigPolicyRepository:
    """Read-side repository for AppConfigPolicy.

    Any authenticated user may read a policy — admin operations
    (create / update / purge / search) live on
    `AppConfigPolicyAdminRepository`. Retry + metric policies are
    applied at the DB-source layer (see
    :mod:`...app_config_policy.db_source.db_source`).
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigPolicyDBSource(db)

    async def get(self, config_name: str) -> AppConfigPolicyData | None:
        return await self._db_source.get(config_name)

    async def get_by_id(self, id: uuid.UUID) -> AppConfigPolicyData | None:
        return await self._db_source.get_by_id(id)
