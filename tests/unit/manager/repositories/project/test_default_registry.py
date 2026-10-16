"""Tests for project default registry writes using a real database."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.association_container_registries_groups.updaters import (
    ProjectDefaultRegistryUpdater,
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
from ai.backend.manager.repositories.ops.v2.project.provider import ProjectOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class _ProjectRegistries:
    project_id: ProjectID
    first_registry_id: ContainerRegistryID
    second_registry_id: ContainerRegistryID


class TestProjectWriteOps:
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
    def provider(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ProjectOpsProvider:
        return ProjectOpsProvider(db_with_cleanup)

    @pytest.fixture
    async def registries(self, db_with_cleanup: ExtendedAsyncSAEngine) -> _ProjectRegistries:
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
        self, provider: ProjectOpsProvider, registries: _ProjectRegistries
    ) -> _ProjectRegistries:
        async with provider.write_ops() as ops:
            await ops.update_default_registry_flags(
                ProjectDefaultRegistryUpdater(
                    project_id=registries.project_id,
                    previous_registry_id=None,
                    registry_id=registries.first_registry_id,
                )
            )
        return registries

    @pytest.fixture
    async def missing_registry_access(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        provider: ProjectOpsProvider,
        registries: _ProjectRegistries,
        has_default: bool,
    ) -> _ProjectRegistries:
        if has_default:
            async with provider.write_ops() as ops:
                await ops.update_default_registry_flags(
                    ProjectDefaultRegistryUpdater(
                        project_id=registries.project_id,
                        previous_registry_id=None,
                        registry_id=registries.first_registry_id,
                    )
                )
        async with db_with_cleanup.begin_session() as session:
            await session.execute(
                sa.delete(AssociationContainerRegistriesGroupsRow).where(
                    AssociationContainerRegistriesGroupsRow.registry_id
                    == registries.second_registry_id
                )
            )
        return registries

    @pytest.fixture
    async def registry_rejecting_default(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        configured_registries: _ProjectRegistries,
    ) -> AsyncIterator[_ProjectRegistries]:
        async with db_with_cleanup.begin() as conn:
            await conn.execute(
                sa.text(
                    "ALTER TABLE association_container_registries_groups ADD CONSTRAINT test_refuse_default "
                    f"CHECK (registry_id <> '{configured_registries.second_registry_id}'::uuid OR NOT is_default)"
                )
            )
        try:
            yield configured_registries
        finally:
            async with db_with_cleanup.begin() as conn:
                await conn.execute(
                    sa.text(
                        "ALTER TABLE association_container_registries_groups DROP CONSTRAINT test_refuse_default"
                    )
                )

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

    async def test_assign_default_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        provider: ProjectOpsProvider,
        registries: _ProjectRegistries,
    ) -> None:
        async with provider.write_ops() as ops:
            await ops.update_default_registry_flags(
                ProjectDefaultRegistryUpdater(
                    project_id=registries.project_id,
                    previous_registry_id=None,
                    registry_id=registries.first_registry_id,
                )
            )
        assert await self._default_flags(db_with_cleanup, registries) == {
            registries.first_registry_id: True,
            registries.second_registry_id: False,
        }

    async def test_switch_default_with_duplicate_registry_names(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        provider: ProjectOpsProvider,
        configured_registries: _ProjectRegistries,
    ) -> None:
        async with provider.write_ops() as ops:
            await ops.update_default_registry_flags(
                ProjectDefaultRegistryUpdater(
                    project_id=configured_registries.project_id,
                    previous_registry_id=configured_registries.first_registry_id,
                    registry_id=configured_registries.second_registry_id,
                )
            )
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.first_registry_id: False,
            configured_registries.second_registry_id: True,
        }

    async def test_clear_default_preserves_access(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        provider: ProjectOpsProvider,
        configured_registries: _ProjectRegistries,
    ) -> None:
        async with provider.write_ops() as ops:
            await ops.update_default_registry_flags(
                ProjectDefaultRegistryUpdater(
                    project_id=configured_registries.project_id,
                    previous_registry_id=configured_registries.first_registry_id,
                    registry_id=None,
                )
            )
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.first_registry_id: False,
            configured_registries.second_registry_id: False,
        }

    @pytest.mark.parametrize("has_default", [False, True], ids=["without-default", "with-default"])
    async def test_missing_association_is_not_created(
        self,
        provider: ProjectOpsProvider,
        db_with_cleanup: ExtendedAsyncSAEngine,
        missing_registry_access: _ProjectRegistries,
        has_default: bool,
    ) -> None:
        previous_registry_id = missing_registry_access.first_registry_id if has_default else None
        with pytest.raises(InvalidAPIParameters, match="has no access association"):
            async with provider.write_ops() as ops:
                await ops.update_default_registry_flags(
                    ProjectDefaultRegistryUpdater(
                        project_id=missing_registry_access.project_id,
                        previous_registry_id=previous_registry_id,
                        registry_id=missing_registry_access.second_registry_id,
                    )
                )
        assert await self._default_flags(db_with_cleanup, missing_registry_access) == {
            missing_registry_access.first_registry_id: has_default
        }

    async def test_stale_previous_registry_is_rejected(
        self,
        provider: ProjectOpsProvider,
        db_with_cleanup: ExtendedAsyncSAEngine,
        configured_registries: _ProjectRegistries,
    ) -> None:
        with pytest.raises(InvalidAPIParameters, match="changed"):
            async with provider.write_ops() as ops:
                await ops.update_default_registry_flags(
                    ProjectDefaultRegistryUpdater(
                        project_id=configured_registries.project_id,
                        previous_registry_id=None,
                        registry_id=configured_registries.second_registry_id,
                    )
                )
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.first_registry_id: True,
            configured_registries.second_registry_id: False,
        }

    async def test_concurrent_initial_assignments_keep_one_default(
        self,
        provider: ProjectOpsProvider,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registries: _ProjectRegistries,
    ) -> None:
        async def assign(registry_id: ContainerRegistryID) -> None:
            async with provider.write_ops() as ops:
                await ops.update_default_registry_flags(
                    ProjectDefaultRegistryUpdater(
                        project_id=registries.project_id,
                        previous_registry_id=None,
                        registry_id=registry_id,
                    )
                )

        async with asyncio.timeout(10):
            results = await asyncio.gather(
                assign(registries.first_registry_id),
                assign(registries.second_registry_id),
                return_exceptions=True,
            )
        assert sum(result is None for result in results) == 1
        assert (
            sum(
                isinstance(result, (InvalidAPIParameters, sa.exc.IntegrityError))
                for result in results
            )
            == 1
        )
        remaining = await self._default_flags(db_with_cleanup, registries)
        assert set(remaining) == {registries.first_registry_id, registries.second_registry_id}
        assert sum(remaining.values()) == 1

    async def test_second_default_is_rejected(
        self, db_with_cleanup: ExtendedAsyncSAEngine, configured_registries: _ProjectRegistries
    ) -> None:
        with pytest.raises(sa.exc.IntegrityError):
            async with db_with_cleanup.begin_session() as session:
                await session.execute(
                    sa.update(AssociationContainerRegistriesGroupsRow)
                    .where(
                        AssociationContainerRegistriesGroupsRow.registry_id
                        == configured_registries.second_registry_id
                    )
                    .values(is_default=True)
                )
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.first_registry_id: True,
            configured_registries.second_registry_id: False,
        }

    async def test_failure_between_flags_rolls_back(
        self,
        provider: ProjectOpsProvider,
        db_with_cleanup: ExtendedAsyncSAEngine,
        registry_rejecting_default: _ProjectRegistries,
    ) -> None:
        with pytest.raises(sa.exc.IntegrityError):
            async with provider.write_ops() as ops:
                await ops.update_default_registry_flags(
                    ProjectDefaultRegistryUpdater(
                        project_id=registry_rejecting_default.project_id,
                        previous_registry_id=registry_rejecting_default.first_registry_id,
                        registry_id=registry_rejecting_default.second_registry_id,
                    )
                )
        assert await self._default_flags(db_with_cleanup, registry_rejecting_default) == {
            registry_rejecting_default.first_registry_id: True,
            registry_rejecting_default.second_registry_id: False,
        }

    async def test_relation_purge_removes_default(
        self, db_with_cleanup: ExtendedAsyncSAEngine, configured_registries: _ProjectRegistries
    ) -> None:
        async with RelationOpsProvider(db_with_cleanup).write_ops() as ops:
            await ops.purge_relations(
                ContainerRegistryProjectPurger(),
                [(configured_registries.project_id, configured_registries.first_registry_id)],
            )
        assert await self._default_flags(db_with_cleanup, configured_registries) == {
            configured_registries.second_registry_id: False
        }
