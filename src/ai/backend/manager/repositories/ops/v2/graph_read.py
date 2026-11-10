"""The read primitives over the RBAC graph, bound to a single session.

The mirror of :mod:`~.graph_write`: that module states own and govern, this one reads
them back. Ownership is the ``scope -> virtual entity -> entity`` path, so which scope
holds an entity is asked here and nowhere else.

Primitives only — no access decision runs on them yet. Image sharing (BA-7667) is the
first caller.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.base import V2OpsBase


class V2GraphReadOpsBase(V2OpsBase):
    """What the graph answers about who holds what."""

    async def scopes_owning(
        self, scope_type: EntityType, entity: EntityIdentifier
    ) -> Sequence[uuid.UUID]:
        """The scopes of ``scope_type`` that own the entity, uncapped — a share is not
        own. Empty where no such scope holds it."""
        return (await self._sess.scalars(self._scopes_owning_query(scope_type, entity))).all()

    async def personal_projects(self, user_ids: Sequence[UserID]) -> dict[UserID, ProjectID]:
        """The personal project of each named user, keyed by the user; one without a
        project is absent.

        Provenance answers which project is a user's own. What that project owns is the
        graph's answer, never this one's.
        """
        if not user_ids:
            return {}
        rows = await self._sess.execute(
            sa.select(ProjectRow.creator_id, ProjectRow.id).where(
                ProjectRow.creator_id.in_(user_ids),
                ProjectRow.type == ProjectType.PERSONAL,
            )
        )
        return {row.creator_id: row.id for row in rows}

    def _scopes_owning_query(
        self, scope_type: EntityType, entity: EntityIdentifier
    ) -> sa.Select[tuple[uuid.UUID]]:
        membership = EntityMembershipRow.__table__
        scope = VirtualEntityRow.__table__.alias("owning_scope_node")
        member = VirtualEntityRow.__table__.alias("owned_entity_node")
        return (
            sa.select(scope.c.entity_id)
            .select_from(membership)
            .join(scope, membership.c.virtual_entity_id == scope.c.id)
            .join(member, membership.c.member_entity_id == member.c.id)
            .where(
                scope.c.entity_type == scope_type,
                member.c.entity_type == entity.entity_type(),
                member.c.entity_id == entity,
                membership.c.capped.is_(False),
            )
        )
