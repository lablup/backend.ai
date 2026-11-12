"""The domain repository's searches over domain container registry relations, against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain_container_registry_relation.row import (
    DomainContainerRegistryRelationRow,
)
from ai.backend.manager.models.domain_container_registry_relation.scopes import (
    DomainContainerRegistryRelationTarget,
)
from ai.backend.manager.models.domain_container_registry_relation.searchable_fields import (
    DomainContainerRegistryRelationSearchableFields,
)
from ai.backend.manager.models.domain_container_registry_relation.searchers import (
    DomainContainerRegistryRelationSearcher,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class _Relations:
    """Domain ``both`` is related to both registries, domain ``shared_only`` to ``shared``."""

    both: DomainID
    shared_only: DomainID
    shared: ContainerRegistryID
    other: ContainerRegistryID


class TestDomainContainerRegistryRelationSearch:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [DomainRow, ContainerRegistryRow, DomainContainerRegistryRelationRow],
        ):
            yield database_connection

    @pytest.fixture
    async def relations(self, db: ExtendedAsyncSAEngine) -> _Relations:
        relations = _Relations(
            both=DomainID(uuid.uuid4()),
            shared_only=DomainID(uuid.uuid4()),
            shared=ContainerRegistryID(uuid.uuid4()),
            other=ContainerRegistryID(uuid.uuid4()),
        )
        async with db.begin_session() as sess:
            for name, domain_id in (
                ("both", relations.both),
                ("shared-only", relations.shared_only),
            ):
                sess.add(DomainRow(id=domain_id, name=name, description=None, is_active=True))
            for project, registry_id in (("shared", relations.shared), ("other", relations.other)):
                sess.add(
                    ContainerRegistryRow(
                        id=registry_id,
                        url="https://cr.example.com",
                        registry_name="cr.example.com",
                        type=ContainerRegistryType.DOCKER,
                        project=project,
                    )
                )
            await sess.flush()
            for domain_id, registry_id in (
                (relations.both, relations.shared),
                (relations.both, relations.other),
                (relations.shared_only, relations.shared),
            ):
                sess.add(
                    DomainContainerRegistryRelationRow(
                        domain_id=domain_id, container_registry_id=registry_id
                    )
                )
        return relations

    @pytest.fixture
    def repository(self, db: ExtendedAsyncSAEngine) -> DomainRepository:
        return DomainRepository(db=db, domain_ops_provider=DomainOpsProvider(db))

    async def test_scoped_search_reads_the_named_domain_alone(
        self, repository: DomainRepository, relations: _Relations
    ) -> None:
        result = await repository.scoped_search_container_registry_relations(
            ScopedSearcher(
                scopes=[DomainContainerRegistryRelationTarget(relations.both)],
                used_by=(),
                searcher=DomainContainerRegistryRelationSearcher(pagination=NoPagination()),
            )
        )

        assert {(item.domain_id, item.container_registry_id) for item in result.items} == {
            (relations.both, relations.shared),
            (relations.both, relations.other),
        }

    async def test_scoped_search_is_narrowed_by_a_used_registry(
        self, repository: DomainRepository, relations: _Relations
    ) -> None:
        usage = DomainContainerRegistryRelationSearchableFields.linked.usage
        result = await repository.scoped_search_container_registry_relations(
            ScopedSearcher(
                scopes=[DomainContainerRegistryRelationTarget(relations.both)],
                used_by=[usage.container_registries.uses(relations.other)],
                searcher=DomainContainerRegistryRelationSearcher(pagination=NoPagination()),
            )
        )

        assert [(item.domain_id, item.container_registry_id) for item in result.items] == [
            (relations.both, relations.other)
        ]

    async def test_global_search_reads_every_domain_of_a_used_registry(
        self, repository: DomainRepository, relations: _Relations
    ) -> None:
        usage = DomainContainerRegistryRelationSearchableFields.linked.usage
        result = await repository.global_search_container_registry_relations(
            GlobalSearcher(
                used_by=[usage.container_registries.uses(relations.shared)],
                searcher=DomainContainerRegistryRelationSearcher(pagination=NoPagination()),
            )
        )

        assert {(item.domain_id, item.container_registry_id) for item in result.items} == {
            (relations.both, relations.shared),
            (relations.shared_only, relations.shared),
        }
