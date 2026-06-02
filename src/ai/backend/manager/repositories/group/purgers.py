from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityBatchPurgerSpec


@dataclass
class GroupKernelBatchPurgerSpec(BatchPurgerSpec[KernelRow]):
    """PurgerSpec for deleting all kernels belonging to a group."""

    group_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[KernelRow]]:
        return sa.select(KernelRow).where(KernelRow.group_id == self.group_id)


@dataclass
class GroupSessionBatchPurgerSpec(BatchPurgerSpec[SessionRow]):
    """PurgerSpec for deleting all sessions belonging to a group."""

    group_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
        return sa.select(SessionRow).where(SessionRow.group_id == self.group_id)


@dataclass
class SessionByIdsBatchPurgerSpec(BatchPurgerSpec[SessionRow]):
    """PurgerSpec for deleting sessions by their IDs."""

    session_ids: Sequence[UUID]

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[SessionRow]]:
        return sa.select(SessionRow).where(SessionRow.id.in_(self.session_ids))


@dataclass
class GroupEndpointBatchPurgerSpec(BatchPurgerSpec[EndpointRow]):
    """PurgerSpec for deleting all endpoints belonging to a group."""

    project_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[EndpointRow]]:
        return sa.select(EndpointRow).where(EndpointRow.project == self.project_id)


@dataclass
class GroupBatchPurgerSpec(RBACEntityBatchPurgerSpec[GroupRow]):
    """PurgerSpec for deleting a group with RBAC scope/permission cleanup."""

    group_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[GroupRow]]:
        return sa.select(GroupRow).where(GroupRow.id == self.group_id)

    @override
    def element_type(self) -> RBACElementType:
        return RBACElementType.PROJECT


@dataclass
class UsersForProjectPurgerSpec(BatchPurgerSpec[AssociationScopesEntitiesRow]):
    """PurgerSpec for removing user-project memberships (PROJECT/USER ASE rows)."""

    user_uuids: list[UUID]
    project_id: UUID

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[AssociationScopesEntitiesRow]]:
        entity_ids = [str(uid) for uid in self.user_uuids]
        return sa.select(AssociationScopesEntitiesRow).where(
            AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
            AssociationScopesEntitiesRow.scope_id == str(self.project_id),
            AssociationScopesEntitiesRow.entity_type == EntityType.USER,
            AssociationScopesEntitiesRow.entity_id.in_(entity_ids),
        )
