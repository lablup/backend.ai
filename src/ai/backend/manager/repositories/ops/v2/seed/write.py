"""Seed writes: each item's rows inserted unless a row holds their key, or upserted, one
savepoint per item. A relation or roster item goes through the primitive its API uses."""

from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.errors.permission import VirtualEntityNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError, RepositoryIntegrityError
from ai.backend.manager.errors.resource import ProjectMemberNotJoinableError
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.relation.write import V2RelationWriteOps
from ai.backend.manager.repositories.ops.v2.resource_policy.write import (
    V2ResourcePolicyWriteOps,
)
from ai.backend.manager.repositories.ops.v2.roster.write import V2RosterWriteOps
from ai.backend.manager.repositories.ops.v2.seed.types import (
    SeedItemWrite,
    SeedRelationWrite,
    SeedRosterWrite,
    SeedWrite,
    SeedWriteItemResult,
)


class V2SeedWriteOps(V2RelationWriteOps, V2RosterWriteOps, V2ResourcePolicyWriteOps):
    """The relation, roster and resource policy write ops plus the seed item write.

    A violation a spec maps to a domain error is answered as the violation it was mapped
    from; any other domain error is answered as itself. Either fails its own item and no
    other. A scope with no virtual entity fails its item as a missing row.
    """

    async def partial_write_seed_items(
        self, writes: Sequence[SeedItemWrite], overwrite: bool
    ) -> list[SeedWriteItemResult]:
        """Write each item in its own savepoint, in the order given, so an item refused
        with a :class:`BackendAIError` leaves the rest written. Any other error raises."""
        results: list[SeedWriteItemResult] = []
        for write in writes:
            try:
                async with self._sess.begin_nested():
                    written = await self._write_item(write, overwrite)
            except VirtualEntityNotFound as e:
                missing = ForeignKeyViolationError(
                    str(e), table_name=VirtualEntityRow.__tablename__
                )
                results.append(SeedWriteItemResult(written=False, error=missing))
                continue
            except BackendAIError as e:
                cause = e.__cause__
                error = cause if isinstance(cause, RepositoryIntegrityError) else e
                results.append(SeedWriteItemResult(written=False, error=error))
                continue
            results.append(SeedWriteItemResult(written=written))
        return results

    async def _write_item(self, write: SeedItemWrite, overwrite: bool) -> bool:
        match write:
            case SeedWrite():
                return await self._write_seed_item(write, overwrite)
            case SeedRelationWrite():
                return await self._write_relation_item(write)
            case SeedRosterWrite():
                return await self._write_roster_item(write)
            case _:
                assert_never(write)

    async def _write_relation_item(self, write: SeedRelationWrite) -> bool:
        """Whether the relation row was written. The graph reads are registered either
        way, so a row missing them is filled."""
        [written] = await self.create_relations(write.creator, [(write.scope, write.target)])
        return written

    async def _write_roster_item(self, write: SeedRosterWrite) -> bool:
        """Whether the user joined. A user already on the roster is left as it stands,
        a personal project's owner included; one the roster cannot take fails."""
        if await self._on_roster(write.project_id, write.user_id):
            return False
        if await self.join_members(write.project_id, [write.user_id]):
            return True
        raise ProjectMemberNotJoinableError(
            f"User {write.user_id} cannot join project {write.project_id}"
        )

    async def _on_roster(self, project_id: ProjectID, user_id: UserID) -> bool:
        stmt = sa.select(user_scope_membership_exists(ProjectEntityType(), project_id, user_id))
        return bool(await self._sess.scalar(stmt))

    async def _join_personal_project_owner(self, entity: EntityIdentifier) -> bool:
        """Put a personal project's creator on its roster, as its creation does, unless
        the creator is already there. Whether the creator joined."""
        if not isinstance(entity, ProjectID):
            return False
        project = (
            await self._sess.execute(
                sa.select(ProjectRow.type, ProjectRow.creator_id).where(ProjectRow.id == entity)
            )
        ).one()
        if project.type is not ProjectType.PERSONAL or project.creator_id is None:
            return False
        owner = UserID(project.creator_id)
        if await self._on_roster(entity, owner):
            return False
        await self._join(entity, owner)
        return True

    async def _restate_resource_policy_shares(self, entity: EntityIdentifier) -> None:
        """Lend a written user or project the resource policies it is subject to, as
        its create and update do."""
        match entity:
            case UserID():
                await self.restate_user_resource_policy_share(entity)
                await self.restate_keypair_resource_policy_share(entity)
            case ProjectID():
                await self.restate_project_resource_policy_share(entity)

    async def _write_seed_item(self, write: SeedWrite, overwrite: bool) -> bool:
        """Whether any row was written: inserted, or under an overwrite updated with the
        values its spec states. A field row is written under an entity that was already
        there as well."""
        entity = await self.insert_entity_if_absent(write.upserter)
        written = entity.inserted
        if overwrite and not entity.inserted:
            await self.upsert_entity(write.upserter)
            written = bool(write.upserter.build_update_values())
        if overwrite:
            for purger in write.field_purgers:
                await self.batch_purge_field_entities(entity.entity_id, purger)
        inserted = await self.atomic_insert_field_entities_if_absent(
            entity.entity_id, write.field_upserters
        )
        written = written or any(inserted)
        standing = [
            upserter
            for upserter, is_new in zip(write.field_upserters, inserted, strict=True)
            if not is_new
        ]
        if overwrite and standing:
            await self.atomic_upsert_field_entities(entity.entity_id, standing)
            written = written or any(upserter.build_update_values() for upserter in standing)
        for user_id in write.granted_users:
            granted = await self.grant_roles(user_id, [RoleID(entity.entity_id)])
            written = written or any(granted)
        written = await self._join_personal_project_owner(entity.entity_id) or written
        if written:
            await self._restate_resource_policy_shares(entity.entity_id)
        return written
