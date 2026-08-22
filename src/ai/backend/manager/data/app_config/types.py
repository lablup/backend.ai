from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionID
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier


@dataclass(frozen=True)
class AppConfigData:
    """Merged per-user view of one ``config_name``.

    ``config`` is every visible fragment deep-merged, not the fragments themselves — the
    fragment API answers which scope holds which value. An empty ``config`` therefore means
    either that nothing visible contributed or that everything that did was empty.
    """

    config_name: str
    config: dict[str, Any]


@dataclass(frozen=True)
class AppConfigDefinitionData(EntityData):
    """Domain data for an app config definition — one registered ``config_name``."""

    id: AppConfigDefinitionID
    config_name: str
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass(frozen=True)
class AppConfigAllowListData(EntityData):
    """Domain data for one app config allow-list entry — a per-``(config_name, scope_type)`` write gate.

    ``rank`` is the merge priority applied to every fragment written under the entry
    (low → high; higher wins).
    """

    id: AppConfigAllowListID
    config_name: str
    scope_type: AppConfigScopeType
    rank: int
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass(frozen=True)
class AppConfigFragmentData(EntityData):
    """Domain data for one app config fragment — a single scoped JSON document."""

    id: AppConfigFragmentID
    config_name: str
    scope_id: EntityIdentifier | None
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> AppConfigFragmentID:
        return self.id
