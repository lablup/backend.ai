"""An `idle_checker_assignment` item is linked as the assignment API links one: the
binding row, the scope governing the checker under READ, and the checker reading the
scope."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType, IdleCheckerID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.idle_checker import IdleCheckerAssignmentScopeNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.types import (
    SeedItemWrite,
    SeedWriteItemResult,
)
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.domain.seed import DomainSeed
from ai.backend.manager.seed.idle_checker.seed import IdleCheckerSeed
from ai.backend.manager.seed.idle_checker_assignment.seed import IdleCheckerAssignmentSeed
from ai.backend.manager.seed.project.seed import ProjectSeed
from ai.backend.manager.seed.resource_group.seed import ResourceGroupSeed
from ai.backend.manager.seed.resource_policy.seed import (
    KeyPairResourcePolicySeed,
    ProjectResourcePolicySeed,
    UserResourcePolicySeed,
)
from ai.backend.manager.seed.user.seed import UserSeed

_DOMAIN = DomainID(uuid.UUID("0198a5a0-0000-7000-8000-0000000a0001"))
_USER = UserID(uuid.UUID("0198a5a0-0000-7000-8000-0000000c0001"))
_PROJECT = ProjectID(uuid.UUID("0198a5a0-0000-7000-8000-0000000d0001"))
_RESOURCE_GROUP = ResourceGroupID(uuid.UUID("0198a5a0-0000-7000-8000-0000000e0001"))
_CHECKER = IdleCheckerID(uuid.UUID("0198a5a0-0000-7000-8000-0000000f0001"))

_SCOPES: list[tuple[str, EntityType, uuid.UUID]] = [
    ("domain", DomainEntityType(), _DOMAIN),
    ("project", ProjectEntityType(), _PROJECT),
    ("resource_group", ResourceGroupEntityType(), _RESOURCE_GROUP),
    ("user", UserEntityType(), _USER),
]


def _entities() -> list[SeedItemWrite]:
    """The scopes and the checker the items name, in kind order."""
    return [
        UserResourcePolicySeed.model_validate({
            "uuid": "0198a5a0-0000-7000-8000-0000000b0001",
            "name": "default",
            "max_vfolder_count": 0,
            "max_quota_scope_size": -1,
            "max_session_count_per_model_session": 10,
        }).write(),
        ProjectResourcePolicySeed.model_validate({
            "uuid": "0198a5a0-0000-7000-8000-0000000b0002",
            "name": "default",
            "max_vfolder_count": 0,
            "max_quota_scope_size": -1,
            "max_network_count": 3,
        }).write(),
        KeyPairResourcePolicySeed.model_validate({
            "uuid": "0198a5a0-0000-7000-8000-0000000b0003",
            "name": "default",
            "total_resource_slots": {},
            "max_concurrent_sessions": 5,
            "max_containers_per_session": 1,
            "idle_timeout": 3600,
            "max_pending_session_resource_slots": {},
            "allowed_vfolder_hosts": {},
        }).write(),
        IdleCheckerSeed.model_validate({
            "id": str(_CHECKER),
            "name": "session-lifetime",
            "target_session_types": ["interactive"],
            "spec": {"type": "session_lifetime", "session_lifetime": {"max_lifetime_seconds": 60}},
        }).write(),
        DomainSeed.model_validate({"id": str(_DOMAIN), "name": "default"}).write(),
        UserSeed.model_validate({
            "id": str(_USER),
            "domain_id": str(_DOMAIN),
            "email": "member@example.com",
            "username": "member",
            "password": "member-password",
            "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0001",
            "keypairs": [
                {
                    "access_key": "AKIAMEMBER0000000000",
                    "secret_key": "member-secret",
                    "is_default": True,
                    "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0003",
                }
            ],
        }).write(),
        ProjectSeed.model_validate({
            "id": str(_PROJECT),
            "domain_id": str(_DOMAIN),
            "name": "research",
            "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0002",
        }).write(),
        ResourceGroupSeed.model_validate({
            "id": str(_RESOURCE_GROUP),
            "name": "default",
            "driver": "static",
            "scheduler": "fifo",
        }).write(),
    ]


def _assign(
    scope_type: str, scope_id: uuid.UUID, checker_id: uuid.UUID = _CHECKER, **values: Any
) -> SeedItemWrite:
    return IdleCheckerAssignmentSeed.model_validate({
        "idle_checker_id": str(checker_id),
        "scope_type": scope_type,
        "scope_id": str(scope_id),
        **values,
    }).write()


def _node(entity_type: EntityType, entity_id: uuid.UUID) -> sa.ScalarSelect[Any]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_type == entity_type, VirtualEntityRow.entity_id == entity_id)
        .scalar_subquery()
    )


def _govern(scope_type: EntityType, scope_id: uuid.UUID) -> sa.Select[Any]:
    """The cap the scope governs the checker under."""
    return sa.select(ScopeBindingRow.permission_cap).where(
        ScopeBindingRow.virtual_entity_id == _node(IdleCheckerEntityType(), _CHECKER),
        ScopeBindingRow.scope_entity_id == _node(scope_type, scope_id),
    )


def _share(scope_type: EntityType, scope_id: uuid.UUID) -> sa.Select[Any]:
    """The checker's membership in the scope it reads."""
    return sa.select(EntityMembershipRow.id).where(
        EntityMembershipRow.virtual_entity_id == _node(IdleCheckerEntityType(), _CHECKER),
        EntityMembershipRow.member_entity_id == _node(scope_type, scope_id),
    )


async def _scalars(db: ExtendedAsyncSAEngine, stmt: sa.Select[Any]) -> list[Any]:
    async with db.begin_readonly() as conn:
        return list((await conn.scalars(stmt)).all())


async def _bindings(db: ExtendedAsyncSAEngine) -> list[tuple[uuid.UUID, str, uuid.UUID, bool]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.select(
                IdleCheckerBindingRow.id,
                IdleCheckerBindingRow.scope_type,
                IdleCheckerBindingRow.scope_id,
                IdleCheckerBindingRow.enabled,
            ).order_by(IdleCheckerBindingRow.scope_type)
        )
        return [tuple(row) for row in rows]


@pytest.fixture
async def entities(db: ExtendedAsyncSAEngine, repository: SeedRepository) -> None:
    results = await repository.partial_write(_entities(), overwrite=False)
    assert all(result.error is None for result in results), results


class TestApply:
    @pytest.mark.parametrize(
        ("scope_type", "entity_type", "scope_id"), _SCOPES, ids=[s[0] for s in _SCOPES]
    )
    async def test_a_binding_is_linked_with_its_graph_reads(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        scope_type: str,
        entity_type: EntityType,
        scope_id: uuid.UUID,
    ) -> None:
        results = await repository.partial_write([_assign(scope_type, scope_id)], overwrite=False)

        assert results == [SeedWriteItemResult(written=True)]
        [(_, written_type, written_id, enabled)] = await _bindings(db)
        assert (written_type, written_id, enabled) == (scope_type, scope_id, True)
        assert await _scalars(db, _govern(entity_type, scope_id)) == [Permission.READ]
        assert len(await _scalars(db, _share(entity_type, scope_id))) == 1

    async def test_a_binding_stated_off_starts_off(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        await repository.partial_write(
            [_assign("project", _PROJECT, enabled=False)], overwrite=False
        )

        [(_, _, _, enabled)] = await _bindings(db)
        assert enabled is False

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_applying_again_leaves_the_rows_as_they_are(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        overwrite: bool,
    ) -> None:
        await repository.partial_write([_assign("domain", _DOMAIN)], overwrite=False)
        bindings = await _bindings(db)
        shares = await _scalars(db, _share(DomainEntityType(), _DOMAIN))

        results = await repository.partial_write(
            [_assign("domain", _DOMAIN, enabled=False)], overwrite=overwrite
        )

        assert results == [SeedWriteItemResult(written=False)]
        assert await _bindings(db) == bindings
        assert await _scalars(db, _share(DomainEntityType(), _DOMAIN)) == shares

    async def test_a_missing_scope_fails_alone(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        results = await repository.partial_write(
            [_assign("project", uuid.uuid4()), _assign("project", _PROJECT)], overwrite=False
        )

        assert [result.written for result in results] == [False, True]
        assert isinstance(results[0].error, IdleCheckerAssignmentScopeNotFound)
        assert len(await _bindings(db)) == 1

    async def test_a_missing_checker_fails_alone(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        results = await repository.partial_write(
            [_assign("user", _USER, checker_id=uuid.uuid4()), _assign("user", _USER)],
            overwrite=False,
        )

        assert [result.written for result in results] == [False, True]
        assert isinstance(results[0].error, ForeignKeyViolationError)
        assert len(await _bindings(db)) == 1
