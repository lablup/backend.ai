"""Links between entities, and the roles a user holds.

One repository for both: putting a user in an organization writes a link and grants a
role in one transaction, and a check that guards either has to read through the ops the
write was given. Splitting them would put two transactions where one is needed.

The primitives live on this concern's ops (:class:`V2RBACOpsProvider`) rather than on the
general ones — one repository holds them, whichever domain declared the spec.

Design rationale: `proposals/BEP-1075-entity-relation-operations.md` and BEP-1076.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.permission import RoleNotEnrolledInScope
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
from ai.backend.manager.repositories.ops.v2.rbac.provider import V2RBACOpsProvider
from ai.backend.manager.repositories.ops.v2.rbac.write import V2RBACWriteOps

__all__ = ("RBACRepository",)


class RBACRepository:
    """Links between entities, who is in an organization, and what roles they hold."""

    _ops: V2RBACOpsProvider

    def __init__(self, ops_provider: V2RBACOpsProvider) -> None:
        self._ops = ops_provider

    async def grant_roles(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        role_ids: Collection[RoleID],
        granted_by: UserID | None = None,
    ) -> None:
        """Give a member roles of that organization, leaving the membership alone.

        A named role the organization does not hold is refused. The check reads through
        the same ops the write uses, so nothing stands between the two.
        """
        async with self._ops.write_ops() as w:
            await self._reject_foreign_roles(w, organization, role_ids)
            await w.grant_roles(user_id, role_ids, granted_by)

    async def revoke_roles(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        role_ids: Collection[RoleID],
    ) -> None:
        """Take roles of that organization back from a member."""
        async with self._ops.write_ops() as w:
            await self._reject_foreign_roles(w, organization, role_ids)
            await w.revoke_roles(user_id, role_ids)

    async def enroll(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        creator: RelationCreator[Any],
        role_ids: Collection[RoleID] | None = None,
        granted_by: UserID | None = None,
    ) -> bool:
        """Put the user in the organization and give them its roles.

        ``role_ids`` names what to give; ``None`` gives the organization's auto-assign
        roles, which is what a join with no role named means. Naming a role the
        organization does not hold is the service's to reject — this writes what it is
        given.
        """
        async with self._ops.write_ops() as w:
            if role_ids is not None:
                await self._reject_foreign_roles(w, organization, role_ids)
                granted: list[RoleID] = list(role_ids)
            else:
                granted = list(await w.auto_assign_role_ids_in(organization))
            linked = await w.create_relation(organization, user_id, creator)
            await w.grant_roles(user_id, granted, granted_by)
            return linked

    async def withdraw(
        self,
        organization: EntityIdentifier,
        user_id: UserID,
        purger: RelationPurger[Any],
    ) -> bool:
        """Take the user out of the organization and back its roles out with them.

        Every role enrolled in the organization goes, with nothing recording which of
        them the join gave: a role may only be named from the organization's own, so one
        held by a non-member is not a state that arises.
        """
        async with self._ops.write_ops() as w:
            enrolled = await w.role_ids_enrolled_in(organization)
            await w.revoke_roles(user_id, enrolled)
            return await w.purge_relation(organization, user_id, purger)

    async def _reject_foreign_roles(
        self,
        w: V2RBACWriteOps,
        organization: EntityIdentifier,
        role_ids: Collection[RoleID],
    ) -> None:
        """Refuse any named role the organization does not hold.

        Reads through the ops it was given, so the check and the write it guards share
        one transaction. Membership must not become a path for attaching an unrelated
        role.
        """
        if not role_ids:
            return
        enrolled = set(await w.role_ids_enrolled_in(organization))
        foreign = [role_id for role_id in role_ids if role_id not in enrolled]
        if foreign:
            raise RoleNotEnrolledInScope(
                f"Roles {foreign} are not enrolled in {organization.entity_type()} {organization}"
            )

    async def create_relation(
        self, left: EntityIdentifier, right: EntityIdentifier, creator: RelationCreator[Any]
    ) -> bool:
        """Link the two entities; ``False`` when the pair was already linked."""
        async with self._ops.write_ops() as w:
            return await w.create_relation(left, right, creator)

    async def delete_relation(
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[Any],
    ) -> bool:
        """Switch the pair's relation off; ``False`` when there was none to switch."""
        async with self._ops.write_ops() as w:
            return await w.delete_relation(left, right, updater)

    async def restore_relation(
        self,
        left: EntityIdentifier,
        right: EntityIdentifier,
        updater: RelationLifecycleUpdater[Any],
    ) -> bool:
        """Switch the pair's relation back on; ``False`` when there was none."""
        async with self._ops.write_ops() as w:
            return await w.restore_relation(left, right, updater)

    async def purge_relation(
        self, left: EntityIdentifier, right: EntityIdentifier, purger: RelationPurger[Any]
    ) -> bool:
        """Remove the row linking the pair; ``False`` when there was none to remove."""
        async with self._ops.write_ops() as w:
            return await w.purge_relation(left, right, purger)
