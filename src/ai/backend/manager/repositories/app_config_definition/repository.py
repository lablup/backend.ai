from __future__ import annotations

from ai.backend.manager.repositories.app_config_definition.db_source import (
    AppConfigDefinitionDBSource,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigDefinitionRepository",)


class AppConfigDefinitionRepository:
    """Non-admin (scoped) access to app config definitions; methods to follow."""

    _db_source: AppConfigDefinitionDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigDefinitionDBSource(ops_provider)
