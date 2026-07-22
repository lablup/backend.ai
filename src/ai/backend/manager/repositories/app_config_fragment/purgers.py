"""Purger specs for app config fragment repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurgerSpec
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
