"""A registry allowed on a project is linked through the primitive the registry API
uses, and a project takes one default registry."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.image import ProjectDefaultContainerRegistryConflict
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.creators import ContainerRegistryProjectCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.seed.provider import SeedOpsProvider
from ai.backend.manager.repositories.ops.v2.seed.types import SeedItemWrite, SeedWriteItemResult
from ai.backend.manager.repositories.seed.repository import SeedRepository
from ai.backend.manager.seed.container_registry.seed import ContainerRegistrySeed
from ai.backend.manager.seed.container_registry_project.seed import ContainerRegistryProjectSeed
from ai.backend.manager.seed.domain.seed import DomainSeed
from ai.backend.manager.seed.project.seed import ProjectSeed
from ai.backend.manager.seed.resource_policy.seed import ProjectResourcePolicySeed

_DOMAIN = DomainID(uuid.UUID("0198a5a0-0000-7000-8000-0000000a0001"))
_PROJECT_POLICY = uuid.UUID("0198a5a0-0000-7000-8000-0000000b0002")
_PROJECT = ProjectID(uuid.UUID("0198a5a0-0000-7000-8000-0000000d0001"))
_OTHER_PROJECT = ProjectID(uuid.UUID("0198a5a0-0000-7000-8000-0000000d0002"))
_HARBOR = ContainerRegistryID(uuid.UUID("0198a5a0-0000-7000-8000-0000000c0001"))
_LOCAL = ContainerRegistryID(uuid.UUID("0198a5a0-0000-7000-8000-0000000c0002"))


def _registry(registry_id: ContainerRegistryID, name: str) -> ContainerRegistrySeed:
    return ContainerRegistrySeed.model_validate({
        "id": str(registry_id),
        "registry_name": name,
        "url": f"https://{name}",
        "type": "docker",
        "is_global": False,
    })


def _project(project_id: ProjectID, name: str) -> ProjectSeed:
    return ProjectSeed.model_validate({
        "id": str(project_id),
        "domain_id": str(_DOMAIN),
        "name": name,
        "resource_policy": "default",
    })


def _entities() -> list[SeedItemWrite]:
    return [
        ProjectResourcePolicySeed.model_validate({
            "uuid": str(_PROJECT_POLICY),
            "name": "default",
            "max_vfolder_count": 0,
            "max_quota_scope_size": -1,
            "max_network_count": 3,
        }).write(),
        DomainSeed.model_validate({"id": str(_DOMAIN), "name": "default"}).write(),
        _project(_PROJECT, "research").write(),
        _project(_OTHER_PROJECT, "staging").write(),
        _registry(_HARBOR, "cr.backend.ai").write(),
        _registry(_LOCAL, "localhost").write(),
    ]


def _allow(
    registry_id: ContainerRegistryID, project_id: ProjectID, is_default: bool = False
) -> SeedItemWrite:
    return ContainerRegistryProjectSeed.model_validate({
        "registry_id": str(registry_id),
        "project_id": str(project_id),
        "is_default": is_default,
    }).write()


def _node(entity_type: Any, entity_id: uuid.UUID) -> sa.ScalarSelect[Any]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(VirtualEntityRow.entity_type == entity_type, VirtualEntityRow.entity_id == entity_id)
        .scalar_subquery()
    )


async def _scalars(db: ExtendedAsyncSAEngine, stmt: sa.Select[Any]) -> list[Any]:
    async with db.begin_readonly() as conn:
        return list((await conn.scalars(stmt)).all())


async def _rows(db: ExtendedAsyncSAEngine) -> dict[tuple[uuid.UUID, uuid.UUID], bool]:
    """Each allowed (registry, project) pair with its default flag."""
    row = AssociationContainerRegistriesGroupsRow
    async with db.begin_readonly() as conn:
        result = await conn.execute(sa.select(row.registry_id, row.project_id, row.is_default))
        return {(r.registry_id, r.project_id): r.is_default for r in result}


async def _graph(
    db: ExtendedAsyncSAEngine, registry_id: ContainerRegistryID, project_id: ProjectID
) -> tuple[list[Any], int]:
    """The cap the project governs the registry under, and how many shares the
    registry holds of the project."""
    registry_node = _node(ContainerRegistryEntityType(), registry_id)
    project_node = _node(ProjectEntityType(), project_id)
    governs = await _scalars(
        db,
        sa.select(ScopeBindingRow.permission_cap).where(
            ScopeBindingRow.virtual_entity_id == registry_node,
            ScopeBindingRow.scope_entity_id == project_node,
        ),
    )
    shares = await _scalars(
        db,
        sa.select(EntityMembershipRow.id).where(
            EntityMembershipRow.virtual_entity_id == registry_node,
            EntityMembershipRow.member_entity_id == project_node,
        ),
    )
    return governs, len(shares)


@pytest.fixture
async def entities(db: ExtendedAsyncSAEngine, repository: SeedRepository) -> None:
    results = await repository.partial_write(_entities(), overwrite=False)
    assert all(result.error is None for result in results), results


class TestAllow:
    async def test_a_seeded_allow_matches_one_the_api_links(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        results = await repository.partial_write([_allow(_HARBOR, _PROJECT)], overwrite=False)
        async with SeedOpsProvider(db).write_ops() as w:
            await w.create_relations(ContainerRegistryProjectCreator(), [(_OTHER_PROJECT, _HARBOR)])

        assert results == [SeedWriteItemResult(written=True)]
        assert await _rows(db) == {
            (_HARBOR, _PROJECT): False,
            (_HARBOR, _OTHER_PROJECT): False,
        }
        assert await _graph(db, _HARBOR, _PROJECT) == ([Permission.READ], 1)
        assert await _graph(db, _HARBOR, _OTHER_PROJECT) == ([Permission.READ], 1)

    async def test_a_default_registry_is_written_as_the_default(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        results = await repository.partial_write(
            [_allow(_HARBOR, _PROJECT, is_default=True), _allow(_LOCAL, _PROJECT)],
            overwrite=False,
        )

        assert results == [SeedWriteItemResult(written=True)] * 2
        assert await _rows(db) == {(_HARBOR, _PROJECT): True, (_LOCAL, _PROJECT): False}

    async def test_a_second_default_for_a_project_fails_alone(
        self, db: ExtendedAsyncSAEngine, repository: SeedRepository, entities: None
    ) -> None:
        results = await repository.partial_write(
            [
                _allow(_HARBOR, _PROJECT, is_default=True),
                _allow(_LOCAL, _PROJECT, is_default=True),
                _allow(_LOCAL, _OTHER_PROJECT, is_default=True),
            ],
            overwrite=False,
        )

        assert [result.written for result in results] == [True, False, True]
        assert isinstance(results[1].error, ProjectDefaultContainerRegistryConflict)
        assert await _rows(db) == {
            (_HARBOR, _PROJECT): True,
            (_LOCAL, _OTHER_PROJECT): True,
        }
        assert await _graph(db, _LOCAL, _PROJECT) == ([], 0)

    @pytest.mark.parametrize("overwrite", [False, True], ids=["insert", "overwrite"])
    async def test_applying_a_default_again_leaves_it_as_it_is(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        overwrite: bool,
    ) -> None:
        item = _allow(_HARBOR, _PROJECT, is_default=True)
        await repository.partial_write([item], overwrite=False)

        results = await repository.partial_write([item], overwrite=overwrite)

        assert results == [SeedWriteItemResult(written=False)]
        assert await _rows(db) == {(_HARBOR, _PROJECT): True}

    @pytest.mark.parametrize(
        ("registry_id", "project_id"),
        [
            (ContainerRegistryID(uuid.uuid4()), _PROJECT),
            (_HARBOR, ProjectID(uuid.uuid4())),
        ],
        ids=["missing-registry", "missing-project"],
    )
    async def test_an_allow_naming_a_missing_entity_fails_alone(
        self,
        db: ExtendedAsyncSAEngine,
        repository: SeedRepository,
        entities: None,
        registry_id: ContainerRegistryID,
        project_id: ProjectID,
    ) -> None:
        results = await repository.partial_write(
            [_allow(registry_id, project_id), _allow(_LOCAL, _PROJECT)], overwrite=False
        )

        assert [result.written for result in results] == [False, True]
        assert isinstance(results[0].error, ForeignKeyViolationError)
        assert await _rows(db) == {(_LOCAL, _PROJECT): False}
