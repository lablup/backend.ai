"""Resource policy writes: the read a scope holds on the policy it is subject to.

A policy is a global catalog row, so no scope reaches it on its own. The scope the
policy applies to is lent it as a share capped to read, the way a project's roster
lends a project its members: an uncapped membership would carry the enclosing
scope's admin roles onto a shared catalog row.

The cap grants nothing by itself. What a scope may do with the policy it reaches is
the read its own roles state (``data/permission/seed/roles/``).

Restating is the whole surface: each method reads the policy the scope is subject to
now, drops whatever policy of that type the scope held, and lends the current one.
Reassignment and removal are the same call.
"""

from __future__ import annotations

from typing import Any, ClassVar

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_policy.scopes import (
    ProjectResourcePolicyTarget,
    UserKeypairResourcePolicyTarget,
    UserResourcePolicyTarget,
)
from ai.backend.manager.models.scopes import ScopeTarget
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.cap import V2CapOps
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps

__all__ = ("V2ResourcePolicyWriteOps",)


class V2ResourcePolicyWriteOps(V2WriteOps, V2CapOps):
    """The general write ops plus the share that puts a scope's policy within reach."""

    # A policy is somebody else's row; the scope it applies to only reads it.
    _POLICY_CAP: ClassVar[Permission] = Permission.READ

    async def restate_user_resource_policy_share(self, user_id: UserID) -> None:
        """Lend the user the user resource policy they are subject to."""
        await self._restate(
            user_id,
            UserResourcePolicyEntityType(),
            UserResourcePolicyRow.uuid,
            UserResourcePolicyTarget(user_id=user_id),
        )

    async def restate_keypair_resource_policy_share(self, user_id: UserID) -> None:
        """Lend the user the keypair resource policy the key they authorize with is
        subject to. A keypair is a field of the user, so the user is the scope."""
        await self._restate(
            user_id,
            KeyPairResourcePolicyEntityType(),
            KeyPairResourcePolicyRow.uuid,
            UserKeypairResourcePolicyTarget(user_id=user_id),
        )

    async def restate_project_resource_policy_share(self, project_id: ProjectID) -> None:
        """Lend the project the project resource policy it is subject to."""
        await self._restate(
            project_id,
            ProjectResourcePolicyEntityType(),
            ProjectResourcePolicyRow.uuid,
            ProjectResourcePolicyTarget(project_id=project_id),
        )

    async def _restate(
        self,
        scope: EntityIdentifier,
        entity_type: EntityType,
        id_column: InstrumentedAttribute[Any],
        target: ScopeTarget,
    ) -> None:
        policy = await self._sess.scalar(sa.select(id_column).where(target.to_condition()()))
        await self._drop_shares(scope, entity_type)
        if policy is None:
            return
        # A row written before the graph, or by a data migration, has no node yet.
        await self._provision([scope, policy])
        share_id = await self._reset_share(scope, policy)
        await self._insert_caps(share_id, dict.fromkeys(self._bits_of(self._POLICY_CAP)))

    async def _drop_shares(self, scope: EntityIdentifier, entity_type: EntityType) -> None:
        """Take back every policy of this type the scope was lent. What the scope owns
        is not a share and stays."""
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id == self._node_id_query(scope),
                EntityMembershipRow.member_entity_id.in_(
                    sa.select(VirtualEntityRow.id).where(
                        VirtualEntityRow.entity_type == entity_type
                    )
                ),
                EntityMembershipRow.capped.is_(True),
            )
        )
