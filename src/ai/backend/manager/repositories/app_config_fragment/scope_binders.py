"""RBAC scope binding helpers for app config fragments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_unbinder import RBACScopeEntityUnbinder


def fragment_rbac_scope_ref(scope_type: AppConfigScopeType, scope_id: str) -> RBACElementRef | None:
    """The RBAC scope a fragment belongs to; ``None`` for global-scoped (public) fragments."""
    element = scope_type.to_rbac_element_type()
    if element is None:
        return None
    return RBACElementRef(element, scope_id)


@dataclass
class AppConfigFragmentByIdPurgerSpec(BatchPurgerSpec[AppConfigFragmentRow]):
    """Select a single fragment row (by id) for deletion."""

    fragment_id: AppConfigFragmentID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AppConfigFragmentRow]]:
        return sa.select(AppConfigFragmentRow).where(AppConfigFragmentRow.id == self.fragment_id)


@dataclass
class AppConfigFragmentScopeUnbinder(RBACScopeEntityUnbinder[AppConfigFragmentRow]):
    """Unbind (purge) one fragment from its owning scope.

    A fragment is a config bound at a scope, so purging it is an unbind: the fragment row
    and its RBAC scope association are deleted atomically. A ``public`` fragment is
    global-scoped (``scope_ref`` is ``None``), so only its row is deleted — it never had
    an association.
    """

    fragment_id: AppConfigFragmentID
    fragment_scope_type: AppConfigScopeType
    fragment_scope_id: str

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[AppConfigFragmentRow]:
        return AppConfigFragmentByIdPurgerSpec(fragment_id=self.fragment_id)

    @property
    @override
    def entity_type(self) -> RBACElementType:
        return RBACElementType.APP_CONFIG_FRAGMENT

    @property
    @override
    def scope_ref(self) -> RBACElementRef | None:
        return fragment_rbac_scope_ref(self.fragment_scope_type, self.fragment_scope_id)

    @property
    @override
    def entity_ids(self) -> Sequence[str] | None:
        return [str(self.fragment_id)]
