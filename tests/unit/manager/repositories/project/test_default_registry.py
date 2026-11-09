"""A project's default container registry, against a real database."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.errors.image import ContainerRegistryGroupsAssociationNotFound
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.purgers import ContainerRegistryProjectPurger
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class _ProjectRegistries:
    project_id: ProjectID
    first_registry_id: ContainerRegistryID
    second_registry_id: ContainerRegistryID


class TestProjectDefaultRegistry:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
                VirtualEntityRow,
                ScopeBindingRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ProjectRepository:
        return ProjectRepository(
            db_with_cleanup,
            V2DBOpsProvider(db_with_cleanup),
            ResourcePolicyOpsProvider(db_with_cleanup),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

    @pytest.fixture
    async def registries(self, db_with_cleanup: ExtendedAsyncSAEngine) -> _ProjectRegistries:
        """One project allowed on two registries that share a name."""
        result = _ProjectRegistries(
            ProjectID(uuid4()), ContainerRegistryID(uuid4()), ContainerRegistryID(uuid4())
        )
        async with db_with_cleanup.begin_session() as session:
            session.add(DomainRow(id=DomainID(uuid4()), name="default"))
            session.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await session.flush()
            session.add(
                ProjectRow(
                    id=result.project_id,
                    name="project",
                    domain_name="default",
                    resource_policy="default",
                )
            )
            for registry_id in [result.first_registry_id, result.second_registry_id]:
                session.add(
                    ContainerRegistryRow(
                        id=registry_id,
                        registry_name="same",
                        project="images",
                        url="https://example.com",
                        type=ContainerRegistryType.DOCKER,
                    )
                )
            await session.flush()
            for registry_id in [result.first_registry_id, result.second_registry_id]:
                session.add(
                    AssociationContainerRegistriesGroupsRow(
                        project_id=result.project_id, registry_id=registry_id
                    )
                )
            for entity_type, entity_id in [
                ("project", result.project_id),
                ("container_registry", result.first_registry_id),
                ("container_registry", result.second_registry_id),
            ]:
                session.add(VirtualEntityRow(entity_type=entity_type, entity_id=entity_id))
        return result

    @pytest.fixture
    async def configured_registries(
        self, repository: ProjectRepository, registries: _ProjectRegistries
    ) -> _ProjectRegistries:
        """The first registry set as the default."""
        await repository.switch_default_registry(
            registries.project_id, registries.first_registry_id
        )
        return registries

    @pytest.fixture
    async def second_registry_unlinked(
        self, db_with_cleanup: ExtendedAsyncSAEngine, configured_registries: _ProjectRegistries
    ) -> _ProjectRegistries:
        async with db_with_cleanup.begin_session() as session:
            await session.execute(
                sa.delete(AssociationContainerRegistriesGroupsRow).where(
                    AssociationContainerRegistriesGroupsRow.registry_id
                    == configured_registries.second_registry_id
                )
            )
        return configured_registries

    async def _default_flags(
        self, db_with_cleanup: ExtendedAsyncSAEngine, ids: _ProjectRegistries
    ) -> dict[ContainerRegistryID, bool]:
        async with db_with_cleanup.begin_readonly_session() as session:
            rows = await session.execute(
                sa.select(
                    AssociationContainerRegistriesGroupsRow.registry_id,
                    AssociationContainerRegistriesGroupsRow.is_default,
                ).where(AssociationContainerRegistriesGroupsRow.project_id == ids.project_id)
            )
            return {registry_id: is_default for registry_id, is_default in rows}

    async def test_switch_onto_another_registry_with_the_same_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: ProjectRepository,
        configured_registries: _ProjectRegistries,
    ) -> None:
        await repository.switch_default_registry(
            configured_registries.project_id, configured_registries.second_registry_id
        )
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.first_registry_id: False,
            configured_registries.second_registry_id: True,
        }

    async def test_registry_the_project_is_not_allowed_on_is_refused(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: ProjectRepository,
        second_registry_unlinked: _ProjectRegistries,
    ) -> None:
        with pytest.raises(ContainerRegistryGroupsAssociationNotFound):
            await repository.switch_default_registry(
                second_registry_unlinked.project_id, second_registry_unlinked.second_registry_id
            )
        assert await self._default_flags(db_with_cleanup, second_registry_unlinked) == {
            second_registry_unlinked.first_registry_id: True
        }

    async def test_clear_keeps_the_link(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: ProjectRepository,
        configured_registries: _ProjectRegistries,
    ) -> None:
        await repository.clear_default_registry(configured_registries.project_id)
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.first_registry_id: False,
            configured_registries.second_registry_id: False,
        }

    async def test_concurrent_switches_keep_one_default(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: ProjectRepository,
        registries: _ProjectRegistries,
    ) -> None:
        async with asyncio.timeout(10):
            await asyncio.gather(
                repository.switch_default_registry(
                    registries.project_id, registries.first_registry_id
                ),
                repository.switch_default_registry(
                    registries.project_id, registries.second_registry_id
                ),
            )
        assert sum((await self._default_flags(db_with_cleanup, registries)).values()) == 1

    async def test_purging_the_default_link_leaves_no_default(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        configured_registries: _ProjectRegistries,
    ) -> None:
        async with RelationOpsProvider(db_with_cleanup).write_ops() as ops:
            await ops.purge_relations(
                ContainerRegistryProjectPurger(),
                [(configured_registries.project_id, configured_registries.first_registry_id)],
            )
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.second_registry_id: False
        }
