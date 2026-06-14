"""Types for app-config-policy repository operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.base import (
    ExistenceCheck,
    QueryCondition,
    SearchScope,
)

__all__ = (
    "AppConfigPolicySearchResult",
    "ConfigNameAppConfigPolicySearchScope",
)


@dataclass
class AppConfigPolicySearchResult:
    """Result from searching app-config policies."""

    items: list[AppConfigPolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class ConfigNameAppConfigPolicySearchScope(SearchScope):
    """Policy rows matching a single ``config_name``.

    One scope = one item of a scoped policy query; the repository layer
    combines multiple scopes with ``OR``.

    ``existence_checks`` is empty by ``SearchableActionTarget`` convention —
    RBAC validation already gates entity reachability.
    """

    config_name: str

    @override
    def to_condition(self) -> QueryCondition:
        config_name = self.config_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigPolicyRow.config_name == config_name

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
