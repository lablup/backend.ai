"""Purger specs for app config fragment repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigFragmentSearchScope,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntityBatchPurgerSpec,
    RBACEntityPurgerSpec,
)
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class AppConfigFragmentPurgerSpec(RBACEntityPurgerSpec[AppConfigFragmentRow]):
    """RBAC purge info for one fragment: identifies it so its scope association is cleared."""

    fragment_id: AppConfigFragmentID

    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def pk_value(self) -> AppConfigFragmentID:
        return self.fragment_id

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.APP_CONFIG_FRAGMENT

    @override
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.APP_CONFIG_FRAGMENT, str(self.fragment_id))

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class AppConfigFragmentBatchPurgerByNamesSpec(RBACEntityBatchPurgerSpec[AppConfigFragmentRow]):
    """Selects one scope's fragments for ``config_names``, purged as one batch with their
    RBAC entries."""

    scope: AppConfigFragmentSearchScope
    config_names: Sequence[str]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigFragmentRow]]:
        return (
            sa.select(AppConfigFragmentRow)
            .where(AppConfigFragmentConditions.by_config_names(self.config_names)())
            .where(self.scope.to_condition()())
        )

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.APP_CONFIG_FRAGMENT

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()
