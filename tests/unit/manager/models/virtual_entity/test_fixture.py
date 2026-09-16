"""Tests for the graph nodes a fixture load provisions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables


class TestProvisionFixtureEntities:
    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
                ContainerRegistryRow,
            ],
        ):
            yield database_connection

    def _registry(self, **overrides: Any) -> dict[str, Any]:
        row: dict[str, Any] = {
            "url": "https://cr.backend.ai",
            "registry_name": "cr.backend.ai",
            "type": "harbor2",
            "project": "stable",
        }
        row.update(overrides)
        return row

    async def _nodes(self, db: ExtendedAsyncSAEngine) -> list[VirtualEntityRow]:
        async with db.begin_readonly_session() as sess:
            return list(
                (
                    await sess.scalars(
                        sa.select(VirtualEntityRow).where(
                            VirtualEntityRow.entity_type == ContainerRegistryEntityType()
                        )
                    )
                ).all()
            )

    async def test_gives_a_fixture_row_a_node_owning_and_governing_itself(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        registry_id = uuid.uuid4()
        await populate_fixture(db, {"container_registries": [self._registry(id=str(registry_id))]})

        nodes = await self._nodes(db)
        assert [node.entity_id for node in nodes] == [registry_id]
        async with db.begin_readonly_session() as sess:
            owns = (
                await sess.scalars(
                    sa.select(EntityMembershipRow.member_entity_id).where(
                        EntityMembershipRow.virtual_entity_id == nodes[0].id
                    )
                )
            ).all()
            governed_by = (
                await sess.scalars(
                    sa.select(ScopeBindingRow.scope_entity_id).where(
                        ScopeBindingRow.virtual_entity_id == nodes[0].id
                    )
                )
            ).all()
        assert list(owns) == [nodes[0].id]
        assert list(governed_by) == [nodes[0].id]

    async def test_covers_a_row_whose_id_the_server_defaults(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await populate_fixture(db, {"container_registries": [self._registry()]})

        async with db.begin_readonly_session() as sess:
            registry_id = (await sess.scalars(sa.select(ContainerRegistryRow.id))).one()
        assert [node.entity_id for node in await self._nodes(db)] == [registry_id]

    async def test_a_second_load_adds_nothing(self, db: ExtendedAsyncSAEngine) -> None:
        fixture: dict[str, Any] = {"container_registries": [self._registry(id=str(uuid.uuid4()))]}
        await populate_fixture(db, fixture)
        await populate_fixture(db, fixture)

        nodes = await self._nodes(db)
        assert len(nodes) == 1
        async with db.begin_readonly_session() as sess:
            assert (
                await sess.scalar(sa.select(sa.func.count()).select_from(EntityMembershipRow))
            ) == 1
            assert (await sess.scalar(sa.select(sa.func.count()).select_from(ScopeBindingRow))) == 1

    async def test_keeps_a_node_the_fixture_wrote_itself(self, db: ExtendedAsyncSAEngine) -> None:
        registry_id = uuid.uuid4()
        node_id = uuid.uuid4()
        await populate_fixture(
            db,
            {
                "container_registries": [self._registry(id=str(registry_id))],
                "virtual_entities": [
                    {
                        "id": str(node_id),
                        "entity_type": "container_registry",
                        "entity_id": str(registry_id),
                    }
                ],
            },
        )

        nodes = await self._nodes(db)
        assert [(node.id, node.entity_id) for node in nodes] == [(node_id, registry_id)]
