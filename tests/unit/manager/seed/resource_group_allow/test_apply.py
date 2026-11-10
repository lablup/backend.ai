"""Resource group allow items are written through the relation creators their API uses:
the same row and graph reads, unchanged when applied again, and a missing side fails its
item alone."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.user import KeyPairNotFound
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.seed.types import (
    SeedItemWrite,
    SeedRelationWrite,
    SeedWriteItemResult,
)
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.base import SeedRelationItem
from ai.backend.manager.seed.domain.seed import DomainSeed
from ai.backend.manager.seed.project.seed import ProjectSeed
from ai.backend.manager.seed.resource_group.seed import ResourceGroupSeed
from ai.backend.manager.seed.resource_group_allow.seed import (
    ResourceGroupForDomainSeed,
    ResourceGroupForKeypairSeed,
    ResourceGroupForProjectSeed,
)
from ai.backend.manager.seed.resource_policy.seed import (
    KeyPairResourcePolicySeed,
    ProjectResourcePolicySeed,
    UserResourcePolicySeed,
)
from ai.backend.manager.seed.user.seed import UserSeed

_DOMAIN = DomainID(uuid.UUID("0198a5a0-0000-7000-8000-0000000a0001"))
_OTHER_DOMAIN = DomainID(uuid.UUID("0198a5a0-0000-7000-8000-0000000a0002"))
_MEMBER = UserID(uuid.UUID("0198a5a0-0000-7000-8000-0000000c0001"))
_OTHER_MEMBER = UserID(uuid.UUID("0198a5a0-0000-7000-8000-0000000c0002"))
_MEMBER_KEY = AccessKey("AKIAMEMBER0000000000")
_OTHER_MEMBER_KEY = AccessKey("AKIAOTHERMEMBER00000")
_PROJECT = ProjectID(uuid.UUID("0198a5a0-0000-7000-8000-0000000d0001"))
_OTHER_PROJECT = ProjectID(uuid.UUID("0198a5a0-0000-7000-8000-0000000d0002"))
_RESOURCE_GROUP = ResourceGroupID(uuid.UUID("0198a5a0-0000-7000-8000-0000000e0001"))
_OTHER_RESOURCE_GROUP = ResourceGroupID(uuid.UUID("0198a5a0-0000-7000-8000-0000000e0002"))
_MISSING = uuid.UUID("0198a5a0-0000-7000-8000-0000000f0001")


def _user(user_id: UserID, access_key: AccessKey, name: str) -> UserSeed:
    return UserSeed.model_validate({
        "id": str(user_id),
        "domain_id": str(_DOMAIN),
        "email": f"{name}@example.com",
        "username": name,
        "password": f"{name}-password",
        "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0001",
        "keypairs": [
            {
                "access_key": access_key,
                "secret_key": f"{name}-secret",
                "is_default": True,
                "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0003",
            }
        ],
    })


def _entities() -> list[SeedItemWrite]:
    """The entities the allow items name, in kind order."""
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
        DomainSeed.model_validate({"id": str(_DOMAIN), "name": "default"}).write(),
        DomainSeed.model_validate({"id": str(_OTHER_DOMAIN), "name": "other"}).write(),
        _user(_MEMBER, _MEMBER_KEY, "member").write(),
        _user(_OTHER_MEMBER, _OTHER_MEMBER_KEY, "other").write(),
        *[
            ProjectSeed.model_validate({
                "id": str(project_id),
                "domain_id": str(_DOMAIN),
                "name": name,
                "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0002",
            }).write()
            for project_id, name in ((_PROJECT, "research"), (_OTHER_PROJECT, "ops"))
        ],
        *[
            ResourceGroupSeed.model_validate({
                "id": str(resource_group_id),
                "name": name,
                "driver": "static",
                "scheduler": "fifo",
            }).write()
            for resource_group_id, name in (
                (_RESOURCE_GROUP, "default"),
                (_OTHER_RESOURCE_GROUP, "gpu"),
            )
        ],
    ]


def _domain(domain_id: uuid.UUID, resource_group_id: uuid.UUID) -> ResourceGroupForDomainSeed:
    return ResourceGroupForDomainSeed.model_validate({
        "domain_id": str(domain_id),
        "resource_group_id": str(resource_group_id),
    })


def _project(project_id: uuid.UUID, resource_group_id: uuid.UUID) -> ResourceGroupForProjectSeed:
    return ResourceGroupForProjectSeed.model_validate({
        "project_id": str(project_id),
        "resource_group_id": str(resource_group_id),
    })


def _keypair(
    access_key: str, user_id: uuid.UUID, resource_group_id: uuid.UUID
) -> ResourceGroupForKeypairSeed:
    return ResourceGroupForKeypairSeed.model_validate({
        "access_key": access_key,
        "user_id": str(user_id),
        "resource_group_id": str(resource_group_id),
    })


_KINDS: list[tuple[str, SeedRelationItem, SeedRelationItem]] = [
    (
        "domain",
        _domain(_DOMAIN, _RESOURCE_GROUP),
        _domain(_OTHER_DOMAIN, _RESOURCE_GROUP),
    ),
    (
        "project",
        _project(_PROJECT, _RESOURCE_GROUP),
        _project(_OTHER_PROJECT, _RESOURCE_GROUP),
    ),
    (
        "keypair",
        _keypair(_MEMBER_KEY, _MEMBER, _RESOURCE_GROUP),
        _keypair(_OTHER_MEMBER_KEY, _OTHER_MEMBER, _RESOURCE_GROUP),
    ),
]
_KIND_IDS = [kind for kind, _, _ in _KINDS]
_ITEMS = [item for _, item, _ in _KINDS]


def _node(scope: EntityIdentifier) -> sa.ScalarSelect[Any]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == scope.entity_type(),
            VirtualEntityRow.entity_id == scope,
        )
        .scalar_subquery()
    )


def _relation_write(item: SeedRelationItem) -> SeedRelationWrite:
    write = item.write()
    assert isinstance(write, SeedRelationWrite)
    return write


async def _scalars(db: ExtendedAsyncSAEngine, stmt: sa.Select[Any]) -> list[Any]:
    async with db.begin_readonly() as conn:
        return list((await conn.scalars(stmt)).all())


async def _rows(db: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
    rows: list[uuid.UUID] = []
    for row_class in (
        ResourceGroupForDomainRow,
        ResourceGroupForProjectRow,
        ResourceGroupForKeypairsRow,
    ):
        rows.extend(await _scalars(db, sa.select(row_class.id).order_by(row_class.id)))
    return rows


async def _reads(db: ExtendedAsyncSAEngine, item: SeedRelationItem) -> tuple[Any, ...]:
    """The caps the scope governs the resource group under, and the caps the resource
    group holds of the scope."""
    write = _relation_write(item)
    governs = await _scalars(
        db,
        sa.select(ScopeBindingRow.permission_cap).where(
            ScopeBindingRow.virtual_entity_id == _node(write.target),
            ScopeBindingRow.scope_entity_id == _node(write.scope),
        ),
    )
    shares = await _scalars(
        db,
        sa.select(EntityMembershipCapRow.permission)
        .join(EntityMembershipRow, EntityMembershipRow.id == EntityMembershipCapRow.membership_id)
        .where(
            EntityMembershipRow.virtual_entity_id == _node(write.target),
            EntityMembershipRow.member_entity_id == _node(write.scope),
        ),
    )
    return (governs, shares)


@pytest.fixture
async def entities(db: ExtendedAsyncSAEngine, repository: SeedRepository) -> None:
    results = await repository.partial_write(_entities(), overwrite=False)
    assert all(result.error is None for result in results), results


class TestApply:
    @pytest.mark.parametrize(("kind", "seeded", "linked"), _KINDS, ids=_KIND_IDS)
    async def test_a_seeded_allow_has_the_reads_of_one_the_api_links(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        kind: str,
        seeded: SeedRelationItem,
        linked: SeedRelationItem,
    ) -> None:
        results = await repository.partial_write([seeded.write()], overwrite=False)
        api = _relation_write(linked)
        await RbacRelationRepository(RelationOpsProvider(db)).create(
            [(api.scope, api.target)], api.creator
        )

        assert results == [SeedWriteItemResult(written=True)]
        assert len(await _rows(db)) == 2
        assert await _reads(db, seeded) == ([Permission.READ], [Permission.READ])
        assert await _reads(db, seeded) == await _reads(db, linked)

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_applying_again_leaves_the_rows_as_they_are(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        overwrite: bool,
    ) -> None:
        await repository.partial_write([item.write() for item in _ITEMS], overwrite=False)
        rows = await _rows(db)
        reads = [await _reads(db, item) for item in _ITEMS]

        results = await repository.partial_write(
            [item.write() for item in _ITEMS], overwrite=overwrite
        )

        assert results == [SeedWriteItemResult(written=False)] * len(_ITEMS)
        assert await _rows(db) == rows
        assert [await _reads(db, item) for item in _ITEMS] == reads

    @pytest.mark.parametrize(
        ("item", "error"),
        [
            (_domain(_DOMAIN, _MISSING), ForeignKeyViolationError),
            (_domain(_MISSING, _RESOURCE_GROUP), ForeignKeyViolationError),
            (_project(_PROJECT, _MISSING), ForeignKeyViolationError),
            (_project(_MISSING, _RESOURCE_GROUP), ForeignKeyViolationError),
            (_keypair(_MEMBER_KEY, _MEMBER, _MISSING), ForeignKeyViolationError),
            (_keypair("AKIAMISSING000000000", _MEMBER, _RESOURCE_GROUP), ForeignKeyViolationError),
            (_keypair(_OTHER_MEMBER_KEY, _MEMBER, _RESOURCE_GROUP), KeyPairNotFound),
            (_keypair(_MEMBER_KEY, _MISSING, _RESOURCE_GROUP), KeyPairNotFound),
        ],
        ids=[
            "domain-missing-resource-group",
            "domain-missing-domain",
            "project-missing-resource-group",
            "project-missing-project",
            "keypair-missing-resource-group",
            "keypair-missing-keypair",
            "keypair-held-by-another-user",
            "keypair-missing-user",
        ],
    )
    async def test_an_item_naming_a_missing_side_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        item: SeedRelationItem,
        error: type[Exception],
    ) -> None:
        results = await repository.partial_write(
            [_ITEMS[0].write(), item.write(), _ITEMS[1].write()], overwrite=False
        )

        assert [result.written for result in results] == [True, False, True]
        assert isinstance(results[1].error, error)
        assert len(await _rows(db)) == 2
