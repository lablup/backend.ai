"""Seed helpers for the RBAC virtual-entity chain in DB-backed tests.

Production membership predicates (e.g. ``user_scope_membership_exists``) resolve
through ``virtual_entities`` / ``entity_memberships`` rather than the legacy
association tables, so tests that insert users or project memberships directly
must also seed the chain rows the enrollment path and the backfill migration
produce. Mirrors the component-test ``VirtualEntitySeeder`` with a get-or-create
scope lookup so fixture ordering stays flexible.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.permission.types import Permission, ScopeType
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow


class VirtualEntitySeeder:
    async def get_or_create_scope(
        self, sess: AsyncSession, scope_type: ScopeType, scope_id: uuid.UUID
    ) -> uuid.UUID:
        existing = await sess.scalar(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == scope_type,
                VirtualEntityRow.entity_id == scope_id,
            )
        )
        if existing is not None:
            return existing
        row = VirtualEntityRow(entity_type=scope_type, entity_id=scope_id)
        sess.add(row)
        await sess.flush()
        return row.id

    async def seed_user_scope(self, sess: AsyncSession, user_id: uuid.UUID) -> None:
        """Give a directly-inserted user the chain rows ``create_full_user`` would
        have made: their own virtual entity plus the self membership/binding."""
        scope_id = await self.get_or_create_scope(sess, ScopeType.USER, user_id)
        sess.add(
            EntityMembershipRow(
                virtual_entity_id=scope_id,
                member_entity_id=scope_id,
                capped=False,
            )
        )
        sess.add(
            ScopeBindingRow(
                virtual_entity_id=scope_id,
                scope_entity_id=scope_id,
                permission_cap=None,
            )
        )
        await sess.flush()

    async def enroll_user_in_project(
        self, sess: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Write the chain rows the enrollment path creates for a user-project
        membership: the user joins the project's virtual entity. The project is not bound
        into the user's own virtual entity — a member does not hand the project its
        personal entities."""
        project_scope_id = await self.get_or_create_scope(sess, ScopeType.PROJECT, group_id)
        user_scope_id = await self.get_or_create_scope(sess, ScopeType.USER, user_id)
        sess.add(
            EntityMembershipRow(
                virtual_entity_id=project_scope_id,
                member_entity_id=user_scope_id,
                capped=False,
            )
        )
        await sess.flush()

    async def cap_edge(
        self,
        sess: AsyncSession,
        virtual_entity_id: uuid.UUID,
        member_entity_id: uuid.UUID,
        cap: Permission | None,
    ) -> None:
        """Write a membership edge as a share capped to ``cap`` on every field
        (one cap row per bit; zero rows for a zero cap), or as belonging for ``None``."""
        edge = EntityMembershipRow(
            virtual_entity_id=virtual_entity_id,
            member_entity_id=member_entity_id,
            capped=cap is not None,
        )
        sess.add(edge)
        await sess.flush()
        if cap is None:
            return
        sess.add_all([
            EntityMembershipCapRow(membership_id=edge.id, permission=bit, all_fields=True)
            for bit in Permission
            if bit and cap & bit
        ])
        await sess.flush()

    async def edge_cap(
        self, sess: AsyncSession, virtual_entity_id: uuid.UUID, member_entity_id: uuid.UUID
    ) -> Permission | None:
        """The every-field cap of an edge as a mask; ``None`` for a belonging edge."""
        edge = (
            await sess.execute(
                sa.select(EntityMembershipRow.id, EntityMembershipRow.capped).where(
                    EntityMembershipRow.virtual_entity_id == virtual_entity_id,
                    EntityMembershipRow.member_entity_id == member_entity_id,
                )
            )
        ).one_or_none()
        if edge is None or not edge.capped:
            return None
        bits = (
            await sess.scalars(
                sa.select(EntityMembershipCapRow.permission).where(
                    EntityMembershipCapRow.membership_id == edge.id,
                    EntityMembershipCapRow.all_fields.is_(True),
                )
            )
        ).all()
        mask = Permission.NONE
        for bit in bits:
            mask |= bit
        return mask
