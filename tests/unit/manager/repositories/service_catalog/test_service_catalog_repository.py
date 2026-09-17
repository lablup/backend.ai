from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.service_catalog import ServiceCatalogEntityType
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.service_catalog.creators import ServiceCatalogEndpointCreator
from ai.backend.manager.models.service_catalog.row import (
    ServiceCatalogEndpointRow,
    ServiceCatalogRow,
)
from ai.backend.manager.models.service_catalog.upserters import ServiceCatalogUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.service_catalog.repository import ServiceCatalogRepository
from ai.backend.testutils.db import with_tables


class TestServiceCatalogRepositoryRegister:
    @pytest.fixture
    async def db_with_tables(
        self,
        global_entity_ids: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            global_entity_ids,
            [
                ServiceCatalogRow,
                ServiceCatalogEndpointRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
            ],
        ):
            yield global_entity_ids

    @pytest.fixture
    def repository(self, db_with_tables: ExtendedAsyncSAEngine) -> ServiceCatalogRepository:
        return ServiceCatalogRepository(V2DBOpsProvider(db_with_tables))

    def _upserter(self, version: str) -> ServiceCatalogUpserter:
        return ServiceCatalogUpserter(
            service_group="manager",
            instance_id="mgr-001",
            display_name="Manager 1",
            version=version,
            labels={},
            startup_time=datetime(2026, 1, 15, tzinfo=UTC),
            config_hash="abc",
        )

    def _endpoint(self, role: str) -> ServiceCatalogEndpointCreator:
        return ServiceCatalogEndpointCreator(
            role=role,
            scope="private",
            address="10.0.0.1",
            port=8080,
            protocol="grpc",
            metadata={},
        )

    async def test_new_service_is_put_in_the_graph_in_the_global_scope(
        self,
        repository: ServiceCatalogRepository,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        service_id = await repository.register(self._upserter("1"), [self._endpoint("main")])

        async with db_with_tables.begin_readonly_session() as session:
            node_id = await session.scalar(
                sa.select(VirtualEntityRow.id).where(
                    VirtualEntityRow.entity_type == ServiceCatalogEntityType(),
                    VirtualEntityRow.entity_id == service_id,
                )
            )
            holders = (
                await session.scalars(
                    sa.select(EntityMembershipRow.virtual_entity_id).where(
                        EntityMembershipRow.member_entity_id == node_id
                    )
                )
            ).all()
            global_node_id = await session.scalar(
                sa.select(VirtualEntityRow.id).where(
                    VirtualEntityRow.entity_type == GlobalEntityType(),
                    VirtualEntityRow.entity_id == global_entity_id(GlobalEntityName.GLOBAL),
                )
            )
        assert node_id is not None
        assert set(holders) == {node_id, global_node_id}

    async def test_reregistration_keeps_the_node_and_replaces_endpoints(
        self,
        repository: ServiceCatalogRepository,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        first_id = await repository.register(
            self._upserter("1"), [self._endpoint("main"), self._endpoint("health")]
        )

        second_id = await repository.register(self._upserter("2"), [self._endpoint("main")])

        async with db_with_tables.begin_readonly_session() as session:
            roles = (
                await session.scalars(
                    sa.select(ServiceCatalogEndpointRow.role).where(
                        ServiceCatalogEndpointRow.service_id == second_id
                    )
                )
            ).all()
            nodes = await session.scalar(
                sa.select(sa.func.count())
                .select_from(VirtualEntityRow)
                .where(VirtualEntityRow.entity_type == ServiceCatalogEntityType())
            )
            version = await session.scalar(
                sa.select(ServiceCatalogRow.version).where(ServiceCatalogRow.id == second_id)
            )
        assert second_id == first_id
        assert roles == ["main"]
        assert nodes == 1
        assert version == "2"
