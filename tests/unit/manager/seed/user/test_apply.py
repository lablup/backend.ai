"""`mgr seed apply` writes the user files through the user and keypair upserters."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.models.hasher.factory import compare_to_hashed_password
from ai.backend.manager.models.keypair.creators import DefaultKeypairCreator
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedApplier, SeedPlan, SeedPlanner
from ai.backend.manager.seed.types import SeedKind
from ai.backend.manager.seed.user.seed import UserKeypairSeed, UserSeed

# A graph edge with each end named by its entity, the user under test as "self".
type _Edge = tuple[str, str, str]
type _User = tuple[str, str, str, str | None, str]
type _Keypair = tuple[uuid.UUID, SecretValue, bool, bool, bool, str, int]


@pytest.fixture
def plan(user_seed_dir: Path) -> SeedPlan:
    return SeedPlanner(create_seed_kind_registry()).plan([user_seed_dir])


@pytest.fixture
async def applied(repository: SeedRepository, plan: SeedPlan) -> None:
    """The user files applied, with the domains and the policies they refer to."""
    await SeedApplier(repository).apply(plan, overwrite=False)


@pytest.fixture
def admin(plan: SeedPlan, admin_user_id: str) -> UserSeed:
    [seed] = [seed for seed in _seeds(plan) if str(seed.id) == admin_user_id]
    return seed


@pytest.fixture
async def runtime_user_id(db: ExtendedAsyncSAEngine, applied: None, admin: UserSeed) -> UserID:
    """A user created the way the user service creates one."""
    async with SeedOpsProvider(db).write_ops() as w:
        data = await w.create_role_managed_entity(
            UserCreator(
                email="runtime@example.com",
                username="runtime",
                password=PasswordInfo(
                    password="password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=1_000,
                    salt_size=32,
                ),
                need_password_change=False,
                domain_id=admin.domain_id,
                resource_policy="default",
            )
        )
        await w.create_field(
            UserID(data.id),
            DefaultKeypairCreator(
                secrets=KeyPairSecrets(
                    access_key=AccessKey("AKRUNTIME"),
                    secret_key=SecretValue("SKRUNTIME"),
                    ssh_public_key="ssh-rsa runtime",
                    ssh_private_key="runtime-private-key",
                ),
                is_active=True,
                is_admin=False,
                resource_policy="default",
            ),
        )
        await w.restate_user_resource_policy_share(UserID(data.id))
        await w.restate_keypair_resource_policy_share(UserID(data.id))
    return UserID(data.id)


async def _users(db: ExtendedAsyncSAEngine) -> dict[str, _User]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                UserRow.uuid,
                UserRow.email,
                UserRow.username,
                UserRow.domain_name,
                UserRow.description,
                UserRow.password,
            )
        )
        return {
            str(row.uuid): (row.email, row.username, row.domain_name, row.description, row.password)
            for row in rows
        }


async def _keypairs(db: ExtendedAsyncSAEngine) -> dict[str, _Keypair]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                KeyPairRow.access_key,
                KeyPairRow.user,
                KeyPairRow.secret_key,
                KeyPairRow.is_active,
                KeyPairRow.is_admin,
                KeyPairRow.is_default,
                KeyPairRow.resource_policy,
                KeyPairRow.rate_limit,
            )
        )
        return {
            row.access_key: (
                row.user,
                row.secret_key,
                row.is_active,
                row.is_admin,
                row.is_default,
                row.resource_policy,
                row.rate_limit,
            )
            for row in rows
        }


async def _edges(db: ExtendedAsyncSAEngine, user_id: uuid.UUID) -> set[_Edge]:
    """The ownership and governance edges touching the user's node."""
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
    user_node = (str(UserEntityType()), str(user_id))

    def name(node_id: uuid.UUID) -> str:
        node = nodes[node_id]
        return "self" if node == user_node else ":".join(node)

    edges: set[_Edge] = set()
    for relation, rows in (("owns", memberships), ("governs", bindings)):
        for owner, member in rows:
            if user_node in (nodes[owner], nodes[member]):
                edges.add((relation, name(owner), name(member)))
    return edges


async def _count(db: ExtendedAsyncSAEngine, table: sa.Table) -> int:
    async with db.begin_readonly() as conn:
        return (await conn.execute(sa.select(sa.func.count()).select_from(table))).scalar_one()


def _seeds(plan: SeedPlan) -> list[UserSeed]:
    return [item for batch in plan.batches for item in batch.items() if isinstance(item, UserSeed)]


def _stated_keypairs(plan: SeedPlan) -> dict[str, _Keypair]:
    return {
        keypair.access_key: (
            seed.id,
            SecretValue(keypair.secret_key),
            keypair.is_active,
            keypair.is_admin,
            keypair.is_default,
            "default",
            keypair.rate_limit if keypair.rate_limit is not None else 10000,
        )
        for seed in _seeds(plan)
        for keypair in seed.keypairs
    }


class TestApply:
    async def test_an_empty_database_gets_the_seed_rows(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
    ) -> None:
        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert len(results[SeedKind.USER].succeeded) == len(_seeds(plan))
        assert results[SeedKind.USER].failed == []
        users = await _users(db)
        assert {key: user[:4] for key, user in users.items()} == {
            str(seed.id): (seed.email, seed.username, "default", seed.description)
            for seed in _seeds(plan)
        }
        for seed in _seeds(plan):
            assert compare_to_hashed_password(seed.password, users[str(seed.id)][4])
        assert await _keypairs(db) == _stated_keypairs(plan)

    async def test_a_seeded_user_has_the_graph_edges_of_a_created_one(
        self,
        db: ExtendedAsyncSAEngine,
        admin: UserSeed,
        runtime_user_id: UserID,
    ) -> None:
        created = await _edges(db, runtime_user_id)
        assert created
        assert await _edges(db, admin.id) == created

    async def test_no_project_role_or_unstated_keypair_is_written(
        self,
        db: ExtendedAsyncSAEngine,
        plan: SeedPlan,
        applied: None,
    ) -> None:
        assert await _count(db, ProjectRow.__table__) == 0
        assert await _count(db, RoleRow.__table__) == 0
        assert set(await _keypairs(db)) == set(_stated_keypairs(plan))

    async def test_an_existing_user_is_skipped_and_left_as_it_is(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        plan: SeedPlan,
        applied: None,
        admin: UserSeed,
    ) -> None:
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(UserRow).where(UserRow.uuid == admin.id).values(description="edited")
            )
            await sess.execute(sa.update(KeyPairRow).values(is_active=False))
        users = await _users(db)
        keypairs = await _keypairs(db)
        edges = await _edges(db, admin.id)

        results = await SeedApplier(repository).apply(plan, overwrite=False)

        assert results[SeedKind.USER].succeeded == []
        assert len(results[SeedKind.USER].skipped) == len(_seeds(plan))
        assert await _users(db) == users
        assert await _keypairs(db) == keypairs
        assert await _edges(db, admin.id) == edges

    async def test_overwrite_restores_the_seed_values_and_keeps_the_insert_only_ones(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        research_domain_id = DomainID(uuid.UUID("0198a5a0-0000-7000-8000-00000000d002"))
        users = await _users(db)
        keypairs = await _keypairs(db)
        edges = await _edges(db, admin.id)
        async with db.begin_session() as sess:
            await sess.execute(
                sa.update(UserRow)
                .where(UserRow.uuid == admin.id)
                .values(email="edited@example.com", description="edited")
            )
            await sess.execute(sa.update(KeyPairRow).values(is_active=False, is_admin=True))
        moved = admin.model_copy(
            update={
                "domain_id": research_domain_id,
                "password": "another-password",
                "keypairs": [
                    keypair.model_copy(update={"secret_key": "another-secret"})
                    for keypair in admin.keypairs
                ],
            }
        )

        [result] = await repository.partial_write([moved.write()], overwrite=True)

        assert result.written
        assert (await _users(db))[str(admin.id)] == users[str(admin.id)]
        assert {
            key: keypair for key, keypair in (await _keypairs(db)).items() if keypair[0] == admin.id
        } == {key: keypair for key, keypair in keypairs.items() if keypair[0] == admin.id}
        assert await _edges(db, admin.id) == edges

    async def test_allowed_client_ips_are_written_as_networks(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        restricted = admin.model_copy(update={"allowed_client_ip": ["10.0.0.0/8", "192.168.0.*"]})

        [result] = await repository.partial_write([restricted.write()], overwrite=True)

        assert result.error is None
        async with db.begin_readonly() as conn:
            stored = (
                await conn.execute(
                    sa.select(UserRow.allowed_client_ip).where(UserRow.uuid == admin.id)
                )
            ).scalar_one()
        assert stored is not None
        assert [str(cidr.address) for cidr in stored] == ["10.0.0.0/8", "192.168.0.0/24"]

    async def test_overwrite_moves_the_default_keypair(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        swapped = admin.model_copy(
            update={
                "keypairs": [
                    keypair.model_copy(update={"is_default": not keypair.is_default})
                    for keypair in admin.keypairs
                ]
            }
        )

        [result] = await repository.partial_write([swapped.write()], overwrite=True)

        assert result.error is None
        keypairs = await _keypairs(db)
        assert {
            keypair.access_key: keypairs[keypair.access_key][4] for keypair in swapped.keypairs
        } == {keypair.access_key: keypair.is_default for keypair in swapped.keypairs}

    async def test_an_email_already_taken_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        repeated = admin.model_copy(
            update={"id": UserID(uuid.uuid4()), "username": "repeated", "keypairs": []}
        )
        fresh = admin.model_copy(
            update={
                "id": UserID(uuid.uuid4()),
                "email": "fresh@example.com",
                "username": "fresh",
                "keypairs": [],
            }
        )

        results = await repository.partial_write([repeated.write(), fresh.write()], overwrite=False)

        assert [result.error is None for result in results] == [False, True]
        users = await _users(db)
        assert str(repeated.id) not in users
        assert str(fresh.id) in users

    async def test_a_domain_that_is_not_there_fails_the_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        orphan = admin.model_copy(
            update={
                "id": UserID(uuid.uuid4()),
                "email": "orphan@example.com",
                "username": "orphan",
                "domain_id": DomainID(uuid.uuid4()),
                "keypairs": [],
            }
        )

        [result] = await repository.partial_write([orphan.write()], overwrite=False)

        assert result.error is not None
        assert str(orphan.id) not in await _users(db)

    async def test_a_resource_policy_that_is_not_there_fails_the_item(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        orphan = admin.model_copy(
            update={
                "id": UserID(uuid.uuid4()),
                "email": "no-policy@example.com",
                "username": "no-policy",
                "resource_policy_id": UserResourcePolicyUUID(uuid.uuid4()),
                "keypairs": [],
            }
        )

        [result] = await repository.partial_write([orphan.write()], overwrite=False)

        assert result.error is not None
        assert str(orphan.id) not in await _users(db)

    async def test_a_keypair_refused_by_a_constraint_fails_its_user(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        unknown_policy = admin.model_copy(
            update={
                "id": UserID(uuid.uuid4()),
                "email": "policy@example.com",
                "username": "policy",
                "keypairs": [
                    UserKeypairSeed(
                        access_key=AccessKey("AKIAUNKNOWNPOLICY001"),
                        secret_key="secret",
                        resource_policy_id=KeyPairResourcePolicyUUID(uuid.uuid4()),
                    )
                ],
            }
        )

        [result] = await repository.partial_write([unknown_policy.write()], overwrite=False)

        assert result.error is not None
        assert str(unknown_policy.id) not in await _users(db)
        assert "AKIAUNKNOWNPOLICY001" not in await _keypairs(db)

    async def test_a_second_default_keypair_fails_its_user(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        applied: None,
        admin: UserSeed,
    ) -> None:
        two_defaults = admin.model_copy(
            update={
                "id": UserID(uuid.uuid4()),
                "email": "defaults@example.com",
                "username": "defaults",
                "keypairs": [
                    UserKeypairSeed(
                        access_key=AccessKey(f"AKIATWODEFAULTS0000{index}"),
                        secret_key="secret",
                        resource_policy_id=admin.keypairs[0].resource_policy_id,
                        is_default=True,
                    )
                    for index in range(2)
                ],
            }
        )

        [result] = await repository.partial_write([two_defaults.write()], overwrite=False)

        assert result.error is not None
        assert str(two_defaults.id) not in await _users(db)
