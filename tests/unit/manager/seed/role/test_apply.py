"""`mgr seed apply` writes the role files through the role, permission and grant upserters."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.role.seed import RoleSeed
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind

# A graph edge with each end named by its entity, the role under test as "self".
type _Edge = tuple[str, str, str]
type _Role = tuple[str, str | None, str, str, str | None, bool, str, str]
type _Permission = tuple[str, str, int]
type _Grant = tuple[str, str]


@pytest.fixture
def plan(role_kind_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([role_kind_seed_dir])


@pytest.fixture
async def applied(repository: SeedRepository, plan: SeedPlan) -> None:
    """The role files applied, with the scopes and the users they refer to."""
    await SeedApplier(repository).apply(plan, overwrite=False)


@pytest.fixture
def research_member(plan: SeedPlan, research_member_role_id: str) -> RoleSeed:
    [seed] = [seed for seed in _seeds(plan) if str(seed.id) == research_member_role_id]
    return seed


@pytest.fixture
async def runtime_role_id(
    db: ExtendedAsyncSAEngine, applied: None, research_member: RoleSeed
) -> RoleID:
    """A role created in the same project the way the role service creates one."""
    async with SeedOpsProvider(db).write_ops() as w:
        data = await w.create_entity(
            RoleCreator(name="runtime", scope=ProjectID(research_member.scope_id))
        )
    return RoleID(data.id)


async def _roles(db: ExtendedAsyncSAEngine) -> dict[str, _Role]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                RoleRow.id,
                RoleRow.name,
                RoleRow.description,
                RoleRow.scope_type,
                RoleRow.scope_id,
                RoleRow.role_preset_id,
                RoleRow.auto_assign,
                RoleRow.source,
                RoleRow.status,
            )
        )
        return {
            str(row.id): (
                row.name,
                row.description,
                str(row.scope_type),
                str(row.scope_id),
                None if row.role_preset_id is None else str(row.role_preset_id),
                row.auto_assign,
                str(row.source),
                str(row.status),
            )
            for row in rows
        }


async def _permissions(db: ExtendedAsyncSAEngine) -> set[_Permission]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(PermissionRow.role_id, PermissionRow.entity_type, PermissionRow.permission)
        )
        return {(str(row.role_id), str(row.entity_type), int(row.permission)) for row in rows}


async def _grants(db: ExtendedAsyncSAEngine) -> set[_Grant]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.select(UserRoleRow.role_id, UserRoleRow.user_id))
        return {(str(row.role_id), str(row.user_id)) for row in rows}


async def _edges(db: ExtendedAsyncSAEngine, role_id: uuid.UUID) -> set[_Edge]:
    """The ownership and governance edges touching the role's node."""
    async with db.begin_readonly() as conn:
        nodes = {
            row.id: (str(row.entity_type), str(row.entity_id))
            for row in await conn.execute(
                sa.select(
                    VirtualEntityRow.id, VirtualEntityRow.entity_type, VirtualEntityRow.entity_id
                )
            )
        }
        memberships = (
            await conn.execute(
                sa.select(
                    EntityMembershipRow.virtual_entity_id, EntityMembershipRow.member_entity_id
                )
            )
        ).all()
        bindings = (
            await conn.execute(
                sa.select(ScopeBindingRow.virtual_entity_id, ScopeBindingRow.scope_entity_id)
            )
        ).all()
    role_node = (str(RoleEntityType()), str(role_id))

    def name(node_id: uuid.UUID) -> str:
        node = nodes[node_id]
        return "self" if node == role_node else ":".join(node)

    edges: set[_Edge] = set()
    for relation, rows in (("owns", memberships), ("governs", bindings)):
        for owner, member in rows:
            if role_node in (nodes[owner], nodes[member]):
                edges.add((relation, name(owner), name(member)))
    return edges


def _seeds(plan: SeedPlan) -> list[RoleSeed]:
    return [item for batch in plan.batches for item in batch.items() if isinstance(item, RoleSeed)]


def _stated_roles(plan: SeedPlan) -> dict[str, _Role]:
    return {
        str(seed.id): (
            seed.name,
            seed.description,
            str(seed.scope_type),
            str(seed.scope_id),
            None,
            seed.auto_assign,
            "custom",
            "active",
        )
        for seed in _seeds(plan)
    }


def _stated_permissions(plan: SeedPlan) -> set[_Permission]:
    return {
        (str(seed.id), entity_type, int(bit))
        for seed in _seeds(plan)
        for entity_type, mask in seed.permissions.items()
        for bit in mask
    }


def _stated_grants(plan: SeedPlan) -> set[_Grant]:
    return {(str(seed.id), str(user_id)) for seed in _seeds(plan) for user_id in seed.users}


class TestApply:
    async def test_an_empty_database_gets_the_seed_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.ROLE].succeeded) == len(_seeds(plan))
        assert results[SeedKind.ROLE].failed == []
        assert await _roles(db) == _stated_roles(plan)
        assert await _permissions(db) == _stated_permissions(plan)
        assert await _grants(db) == _stated_grants(plan)

    async def test_a_seeded_role_has_the_graph_edges_of_a_created_one(
        self,
        db: ExtendedAsyncSAEngine,
        research_member: RoleSeed,
        runtime_role_id: RoleID,
    ) -> None:
        created = await _edges(db, runtime_role_id)
        assert created
        assert await _edges(db, research_member.id) == created

    async def test_an_existing_role_is_skipped_and_left_as_it_is(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        applied: None,
        research_member: RoleSeed,
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RoleRow)
                .where(RoleRow.id == research_member.id)
                .values(name="edited", auto_assign=False)
            )
        roles = await _roles(db)
        permissions = await _permissions(db)
        grants = await _grants(db)
        edges = await _edges(db, research_member.id)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.ROLE].succeeded == []
        assert len(results[SeedKind.ROLE].skipped) == len(_seeds(plan))
        assert await _roles(db) == roles
        assert await _permissions(db) == permissions
        assert await _grants(db) == grants
        assert await _edges(db, research_member.id) == edges

    async def test_overwrite_restores_the_seed_values_and_keeps_the_insert_only_ones(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        applied: None,
        research_member: RoleSeed,
    ) -> None:
        roles = await _roles(db)
        edges = await _edges(db, research_member.id)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(RoleRow)
                .where(RoleRow.id == research_member.id)
                .values(name="edited", status=RoleStatus.DELETED)
            )
        moved = research_member.model_copy(
            update={"scope_id": uuid.UUID("0198a5a0-0000-7000-8000-00000000e002")}
        )

        [result] = await repository.partial_write([moved.write()], overwrite=True)

        assert result.written
        assert (await _roles(db))[str(research_member.id)] == roles[str(research_member.id)]
        assert await _edges(db, research_member.id) == edges

    async def test_overwrite_drops_the_bits_left_out_on_a_stated_entity_type_only(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        research_member: RoleSeed,
    ) -> None:
        role_id = str(research_member.id)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.insert(PermissionRow).values(
                    role_id=research_member.id, entity_type="image", permission=Permission.READ
                )
            )
        narrowed = research_member.model_copy(
            update={"permissions": {"session": Permission.READ, "vfolder": Permission.NONE}}
        )

        [result] = await repository.partial_write([narrowed.write()], overwrite=True)

        assert result.error is None
        assert {
            permission for permission in await _permissions(db) if permission[0] == role_id
        } == {
            (role_id, "session", int(Permission.READ)),
            (role_id, "image", int(Permission.READ)),
        }

    async def test_overwrite_keeps_a_grant_the_seed_does_not_state(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        applied: None,
        research_member: RoleSeed,
    ) -> None:
        ungranted = research_member.model_copy(update={"users": []})

        [result] = await repository.partial_write([ungranted.write()], overwrite=True)

        assert result.error is None
        assert await _grants(db) == _stated_grants(plan)

    async def test_a_user_that_is_not_there_fails_its_role_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        research_member: RoleSeed,
    ) -> None:
        orphan = research_member.model_copy(
            update={"id": RoleID(uuid.uuid4()), "users": [UserID(uuid.uuid4())]}
        )
        fresh = research_member.model_copy(update={"id": RoleID(uuid.uuid4())})

        results = await repository.partial_write([orphan.write(), fresh.write()], overwrite=False)

        assert [result.error is None for result in results] == [False, True]
        roles = await _roles(db)
        assert str(orphan.id) not in roles
        assert str(fresh.id) in roles

    async def test_a_scope_that_is_not_there_fails_the_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        research_member: RoleSeed,
    ) -> None:
        orphan = research_member.model_copy(
            update={"id": RoleID(uuid.uuid4()), "scope_id": uuid.uuid4()}
        )

        [result] = await repository.partial_write([orphan.write()], overwrite=False)

        assert result.error is not None
        assert str(orphan.id) not in await _roles(db)
