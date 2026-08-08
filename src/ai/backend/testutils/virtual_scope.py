"""Seed helpers for the RBAC virtual-scope chain in DB-backed tests.

Production membership predicates (e.g. ``user_scope_membership_exists``) resolve
through ``virtual_scopes`` / ``entity_memberships`` rather than the legacy
association tables, so tests that insert users or project memberships directly
must also seed the chain rows the enrollment path and the backfill migration
produce. Mirrors the component-test ``VirtualScopeSeeder`` with a get-or-create
scope lookup so fixture ordering stays flexible.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow


class VirtualScopeSeeder:
    async def get_or_create_scope(
        self, sess: AsyncSession, scope_type: ScopeType, scope_id: uuid.UUID
    ) -> uuid.UUID:
        existing = await sess.scalar(
            sa.select(VirtualScopeRow.id).where(
                VirtualScopeRow.scope_type == scope_type,
                VirtualScopeRow.scope_id == scope_id,
            )
        )
        if existing is not None:
            return existing
        row = VirtualScopeRow(scope_type=scope_type, scope_id=scope_id)
        sess.add(row)
        await sess.flush()
        return row.id

    async def seed_user_scope(self, sess: AsyncSession, user_id: uuid.UUID) -> None:
        """Give a directly-inserted user the chain rows ``create_full_user`` would
        have made: their own virtual scope plus the self membership/binding."""
        scope_id = await self.get_or_create_scope(sess, ScopeType.USER, user_id)
        sess.add(
            EntityMembershipRow(
                virtual_scope_id=scope_id,
                entity_type=EntityType.USER,
                entity_id=user_id,
                permission_cap=None,
            )
        )
        sess.add(
            ScopeBindingRow(
                virtual_scope_id=scope_id,
                scope_type=ScopeType.USER,
                scope_id=user_id,
                permission_cap=None,
            )
        )
        await sess.flush()

    async def enroll_user_in_project(
        self, sess: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Write the chain rows the enrollment path creates for a user-project
        membership: the user joins the project's virtual scope and the project is
        bound into the user's own virtual scope."""
        project_scope_id = await self.get_or_create_scope(sess, ScopeType.PROJECT, group_id)
        user_scope_id = await self.get_or_create_scope(sess, ScopeType.USER, user_id)
        sess.add(
            EntityMembershipRow(
                virtual_scope_id=project_scope_id,
                entity_type=EntityType.USER,
                entity_id=user_id,
                permission_cap=None,
            )
        )
        sess.add(
            ScopeBindingRow(
                virtual_scope_id=user_scope_id,
                scope_type=ScopeType.PROJECT,
                scope_id=group_id,
                permission_cap=None,
            )
        )
        await sess.flush()
