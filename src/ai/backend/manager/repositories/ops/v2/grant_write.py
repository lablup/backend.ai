"""Grant writes of the v2 ops: access to an existing entity, offered, handed out and
taken back.

A grant records the entity as a member of the grantee's virtual entity carrying a
permission cap, which is what
``PermissionControllerDBSource._resolve_permissions_for_virtual_entity_group`` clips the
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
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.repositories.ops.v2.write_base import V2WriteOpsBase


class V2GrantWriteOps(V2WriteOpsBase):
    """Grants over existing entities, bound to a single session."""

    async def grant_entities(self, grants: Sequence[EntityGrant]) -> None:
        """Hand each entity to its grantee, bounded by the grant's cap.

        Re-granting rewrites the cap rather than keeping the earlier one: a grant
        states the ceiling that holds now, so a widened or narrowed one has to win.
        A grantee with no virtual entity fails, as every membership write does; the
        entity's node is provisioned if it is missing, since entities created before
        the virtual-entity rollout have none.
        """
        if not grants:
            return
        stmt = pg_insert(EntityMembershipRow).values(await self._grant_values(grants))
        await self._sess.execute(
            stmt.on_conflict_do_update(
                index_elements=["virtual_entity_id", "member_entity_id"],
                set_={"permission_cap": stmt.excluded.permission_cap},
            )
        )

    async def widen_entity_grants(self, grants: Sequence[EntityGrant]) -> None:
        """Add each grant's cap to what the grantee already holds, never taking away.

        Where :meth:`grant_entities` states the ceiling that holds now, this only ever
        raises it: a grantee reached by two offers keeps the wider one, and an offer of
        less than they already have changes nothing. ``None`` means no ceiling, so it
        wins over any mask on either side.
        """
        if not grants:
            return
        stmt = pg_insert(EntityMembershipRow).values(await self._grant_values(grants))
        existing = EntityMembershipRow.permission_cap
        offered = stmt.excluded.permission_cap
        await self._sess.execute(
            stmt.on_conflict_do_update(
                index_elements=["virtual_entity_id", "member_entity_id"],
                set_={
                    "permission_cap": sa.case(
                        (
                            sa.or_(existing.is_(None), offered.is_(None)),
                            sa.null(),
                        ),
                        else_=existing.op("|")(offered),
                    )
                },
            )
        )

    async def _grant_values(self, grants: Sequence[EntityGrant]) -> list[dict[str, object]]:
        await self._provision_entities([g.entity for g in grants])
        node_ids = await self._resolve_virtual_entity_ids([
            *(g.grantee for g in grants),
            *(g.entity for g in grants),
        ])
        return [
            {
                "virtual_entity_id": node_ids[(g.grantee.entity_type(), g.grantee)],
                "member_entity_id": node_ids[(g.entity.entity_type(), g.entity)],
                "permission_cap": g.permission_cap,
            }
            for g in grants
        ]

    async def revoke_entities(
        self, entities: Sequence[EntityIdentifier], grantee: EntityIdentifier
    ) -> None:
        """Take the entities back from the grantee's scope.

        Silent on what was never granted — a revoke states the absence it leaves, not
        that it found something to remove.
        """
        if not entities:
            return
        scope_ids = await self._resolve_virtual_entity_ids([grantee])
        await self._sess.execute(
            sa.delete(EntityMembershipRow).where(
                EntityMembershipRow.virtual_entity_id
                == scope_ids[(grantee.entity_type(), grantee)],
                EntityMembershipRow.member_entity_id.in_(self._virtual_entity_ids_query(entities)),
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

        The grant widens rather than states: an offer is somebody else's, and accepting
        one must not cost the invitee access they already had. Setting a cap exactly is
        :meth:`grant_entities`, which an invitation never reaches.
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
        await self.widen_entity_grants([
            EntityGrant(
                entity=data.target,
                grantee=updater.invitee_user_id,
                permission_cap=data.permission_cap,
            )
        ])
        return data
