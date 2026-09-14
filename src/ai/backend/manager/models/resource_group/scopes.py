"""Operation scopes for resource groups.

A resource group is reachable from three sides — the domains, the projects and the
keypairs it is associated with. Each side is its own scope, and a read naming several
of them sees the union.

None of them checks that the scope exists. A read naming several scopes is answered
from the ones that resolve, so a stale id contributes nothing rather than failing the
whole page.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "DomainResourceGroupOperationScope",
    "ProjectResourceGroupOperationScope",
    "UserResourceGroupOperationScope",
)


@dataclass(frozen=True)
class DomainResourceGroupOperationScope(OperationScope):
    """The resource groups a domain may schedule on."""

    domain_id: DomainID

    @override
    def to_condition(self) -> QueryCondition:
        domain_id = self.domain_id

        # TODO(BA-7571): drop the association term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                ResourceGroupRow.id.in_(
                    sa.select(ResourceGroupForDomainRow.resource_group_id).where(
                        ResourceGroupForDomainRow.domain_id == domain_id
                    )
                ),
                scope_membership_exists(
                    ResourceGroupEntityType(),
                    ResourceGroupRow.id,
                    DomainEntityType(),
                    domain_id,
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class ProjectResourceGroupOperationScope(OperationScope):
    """The resource groups a project may schedule on."""

    project_id: ProjectID

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        # TODO(BA-7571): drop the association term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                ResourceGroupRow.id.in_(
                    sa.select(ResourceGroupForProjectRow.resource_group_id).where(
                        ResourceGroupForProjectRow.group == project_id
                    )
                ),
                scope_membership_exists(
                    ResourceGroupEntityType(),
                    ResourceGroupRow.id,
                    ProjectEntityType(),
                    project_id,
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


@dataclass(frozen=True)
class UserResourceGroupOperationScope(OperationScope):
    """The resource groups a user's keypairs may schedule on.

    Keyed on the user rather than one access key: a keypair carries no permission of
    its own, so the user is what such a read is answered for.
    """

    user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        # TODO(BA-7571): drop the association term once the ownership backfill lands.
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                ResourceGroupRow.id.in_(
                    sa.select(ResourceGroupForKeypairsRow.resource_group_id).where(
                        ResourceGroupForKeypairsRow.access_key.in_(
                            sa.select(KeyPairRow.access_key).where(KeyPairRow.user == user_id)
                        )
                    )
                ),
                scope_membership_exists(
                    ResourceGroupEntityType(),
                    ResourceGroupRow.id,
                    UserEntityType(),
                    user_id,
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
