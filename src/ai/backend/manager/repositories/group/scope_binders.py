from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.group.row import AssocGroupUserRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)
from ai.backend.manager.repositories.group.purgers import UsersForProjectPurgerSpec


@dataclass
class UserProjectEntityUnbinder(RBACScopeEntityUnbinder[AssocGroupUserRow]):
    """Unbind users from a project.

    Deletes association_groups_users rows and corresponding
    AssociationScopesEntitiesRow entries for the given users in the project scope.
    """

    user_uuids: list[UUID]
    project_id: UUID

    @override
    def build_purger_spec(self) -> BatchPurgerSpec[AssocGroupUserRow]:
        return UsersForProjectPurgerSpec(
            user_uuids=self.user_uuids,
            project_id=self.project_id,
        )

    @property
    @override
    def entity_type(self) -> RBACElementType:
        return RBACElementType.USER

    @property
    @override
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.project_id))

    @property
    @override
    def entity_ids(self) -> Sequence[str]:
        return [str(uid) for uid in self.user_uuids]
