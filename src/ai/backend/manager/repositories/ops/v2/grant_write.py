"""Grant writes of the v2 ops: access to an existing entity, offered, handed out and
taken back.

A grant records the entity as a member of the grantee's virtual scope carrying a
permission cap, which is what
``PermissionControllerDBSource._resolve_permissions_for_virtual_scope_group`` clips the
grantee's permissions to. Creation-time belonging is not this: see
``models/specs/AGENTS.md``.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.entity_invitation.types import EntityInvitationData
from ai.backend.manager.models.entity_invitation.updaters import EntityInvitationAcceptUpdater
from ai.backend.manager.models.specs.membership import EntityGrant
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2GrantWriteOps(V2WriteOpsBase):
    """Grants over existing entities, bound to a single session."""

    async def grant_entities(self, grants: Sequence[EntityGrant]) -> None:
        """Hand each entity to its grantee, bounded by the grant's cap.

        Re-granting rewrites the cap rather than keeping the earlier one: a grant
        states the ceiling that holds now, so a widened or narrowed one has to win.
        A grantee with no virtual scope fails, as every membership write does.
        """
        if not grants:
            return
        scope_ids = await self._resolve_virtual_scope_ids([g.grantee for g in grants])
        stmt = pg_insert(EntityMembershipRow).values([
            {
                "virtual_scope_id": scope_ids[(g.grantee.entity_type(), g.grantee)],
                "entity_type": g.entity.entity_type(),
                "entity_id": g.entity,
                "permission_cap": g.permission_cap,
            }
            for g in grants
        ])
        await self._sess.execute(
            stmt.on_conflict_do_update(
                index_elements=["virtual_scope_id", "entity_type", "entity_id"],
                set_={"permission_cap": stmt.excluded.permission_cap},
            )
        )

    async def revoke_entities(
        self, entities: Sequence[EntityIdentifier], grantee: EntityIdentifier
    ) -> None:
        """Take the entities back from the grantee's scope.

        Silent on what was never granted — a revoke states the absence it leaves, not
        that it found something to remove.
        """
        if not entities:
            return
        scope_ids = await self._resolve_virtual_scope_ids([grantee])
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_scope_id == scope_ids[(grantee.entity_type(), grantee)],
                sa.tuple_(EntityMembershipRow.entity_type, EntityMembershipRow.entity_id).in_([
                    (e.entity_type(), e) for e in entities
                ]),
            )
        )

    async def accept_entity_invitation(
        self, updater: EntityInvitationAcceptUpdater
    ) -> EntityInvitationData | None:
        """Settle the invitation as accepted and hand its entity to the invitee.

        ``None`` when nothing was settled — the invitation is gone, already answered,
        or addressed to somebody else; the guards do not say which. Turning one down
        grants nothing and goes through the plain guarded update instead, which is why
        only this direction is a primitive: the settle and the grant cannot come apart.
        """
        row = await self._update_guarded_row_returning(
            updater.row_class,
            updater.target_id_column(),
            updater.target_id_value(),
            updater.guard_conditions(),
            updater.build_values(),
            updater.integrity_error_checks,
        )
        if row is None:
            return None
        data = updater.to_data(row)
        await self.grant_entities([
            EntityGrant(
                entity=data.target(),
                grantee=updater.invitee_user_id,
                permission_cap=data.permission_cap,
            )
        ])
        return data
