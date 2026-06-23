"""Types for app config fragment repository operations (search scopes)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.errors.app_config import AppConfigDefinitionNotFound
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import (
    ExistenceCheck,
    QueryCondition,
    SearchScope,
)

__all__ = ("ConfigNameSearchScope",)


@dataclass(frozen=True)
class ConfigNameSearchScope(SearchScope):
    """Fragments belonging to a single ``config_name``.

    One scope = all fragments registered under one app config name, regardless of their
    ``scope_type`` (public / domain / user). The existence check rejects an unregistered
    ``config_name`` up front so a scoped search cannot silently return nothing.
    """

    config_name: str

    @override
    def to_condition(self) -> QueryCondition:
        config_name = self.config_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AppConfigFragmentRow.config_name == config_name

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return (
            ExistenceCheck(
                column=AppConfigDefinitionRow.config_name,
                value=self.config_name,
                error=AppConfigDefinitionNotFound(
                    f"App config definition {self.config_name!r} not found"
                ),
            ),
        )
