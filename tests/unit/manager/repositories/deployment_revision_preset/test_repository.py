"""Tests for a deployment preset and the slot quantities it owns.

Covers the rank computed inside the INSERT, the slots written with the preset in one
transaction, and update replacing / keeping / clearing them.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.errors.resource import DeploymentRevisionPresetNotFound
from ai.backend.manager.models.base import ensure_all_tables_registered
from ai.backend.manager.models.deployment_revision_preset.creators import (
    RANK_GAP,
    DeploymentPresetCreator,
    PresetResourceSlotCreator,
)
from ai.backend.manager.models.deployment_revision_preset.purgers import DeploymentPresetPurger
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.searchers import (
    PresetResourceSlotSearcher,
)
from ai.backend.manager.models.deployment_revision_preset.updaters import DeploymentPresetUpdater
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow, ResourceSlotTypeRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentPresetRepository,
)
from ai.backend.manager.repositories.deployment_revision_preset.types import (
    DeploymentPresetSlotOperationScope,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

ensure_all_tables_registered()

# Shared runtime variant id: the rank is computed within one variant's presets.
_VARIANT_ID = RuntimeVariantID(uuid4())


def _creator(name: str = "preset-1") -> DeploymentPresetCreator:
    return DeploymentPresetCreator(
        runtime_variant_id=_VARIANT_ID,
        name=name,
        description=None,
        image_id=ImageID(uuid4()),
        model_definition=None,
        resource_opts=[],
        cluster_mode="single-node",
        cluster_size=1,
        startup_command=None,
        bootstrap_script=None,
        environ={},
        runtime_variant_preset_values=[],
        replica_count=1,
        deployment_strategy=DeploymentStrategy.ROLLING,
        deployment_strategy_spec={},
    )


def _slots(*entries: tuple[str, str]) -> list[PresetResourceSlotCreator]:
    return [
        PresetResourceSlotCreator(
            entry=ResourceSlotEntryData(resource_type=name, quantity=quantity)
        )
        for name, quantity in entries
    ]


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            VirtualScopeRow,
            EntityMembershipRow,
            ScopeBindingRow,
            RoleRow,
            PermissionRow,
            RuntimeVariantRow,
            ResourceSlotTypeRow,
            DeploymentRevisionPresetRow,
            PresetResourceSlotRow,
        ],
    ):
        async with database_connection.begin_session() as session:
            session.add(
                RuntimeVariantRow(
                    id=_VARIANT_ID,
                    name="rv-test",
                    default_model_definition=DefaultModelDefinition(),
                )
            )
            session.add_all([
                ResourceSlotTypeRow(slot_name="cpu", slot_type="count"),
                ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"),
            ])
        yield database_connection


@pytest.fixture
def ops(database: ExtendedAsyncSAEngine) -> OpsRepository[DeploymentRevisionPresetData]:
    return OpsRepository(V2DBOpsProvider(database))


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> DeploymentPresetRepository:
    return DeploymentPresetRepository(V2DBOpsProvider(database))


async def _slot_map(
    database: ExtendedAsyncSAEngine, preset_id: DeploymentPresetID
) -> dict[str, Decimal]:
    async with V2DBOpsProvider(database).read_ops() as r:
        result = await r.search_with_scopes(
            (DeploymentPresetSlotOperationScope(preset_id=preset_id),),
            PresetResourceSlotSearcher(pagination=NoPagination()),
        )
    return {item.slot_name: item.quantity for item in result.items}


class TestCreate:
    async def test_writes_the_preset_and_its_slots(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[DeploymentRevisionPresetData],
        repository: DeploymentPresetRepository,
    ) -> None:
        result = await ops.create_global_entity_with_fields(
            _creator(), _slots(("cpu", "2"), ("mem", "1024"))
        )
        assert await _slot_map(database, result.data.id) == {
            "cpu": Decimal("2"),
            "mem": Decimal("1024"),
        }

    async def test_first_preset_takes_the_rank_gap(
        self, ops: OpsRepository[DeploymentRevisionPresetData]
    ) -> None:
        result = await ops.create_global_entity_with_fields(_creator(), _slots(("cpu", "1")))
        assert result.data.rank == RANK_GAP

    async def test_each_preset_takes_the_next_rank(
        self, ops: OpsRepository[DeploymentRevisionPresetData]
    ) -> None:
        first = await ops.create_global_entity_with_fields(_creator("p1"), _slots(("cpu", "1")))
        second = await ops.create_global_entity_with_fields(_creator("p2"), _slots(("cpu", "1")))
        assert second.data.rank == first.data.rank + RANK_GAP


class TestUpdate:
    async def test_a_slot_sequence_replaces_the_whole_set(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[DeploymentRevisionPresetData],
        repository: DeploymentPresetRepository,
    ) -> None:
        created = await ops.create_global_entity_with_fields(_creator(), _slots(("cpu", "2")))

        await repository.update(
            DeploymentPresetUpdater(preset_id=created.data.id),
            _slots(("cpu", "4"), ("mem", "512")),
        )

        assert await _slot_map(database, created.data.id) == {
            "cpu": Decimal("4"),
            "mem": Decimal("512"),
        }

    async def test_none_leaves_the_slots_alone(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[DeploymentRevisionPresetData],
        repository: DeploymentPresetRepository,
    ) -> None:
        created = await ops.create_global_entity_with_fields(_creator(), _slots(("cpu", "2")))

        updated = await repository.update(
            DeploymentPresetUpdater(
                preset_id=created.data.id, name=OptionalState.update("renamed")
            ),
            None,
        )

        assert updated.name == "renamed"
        assert await _slot_map(database, created.data.id) == {"cpu": Decimal("2")}

    async def test_an_empty_sequence_clears_the_slots(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[DeploymentRevisionPresetData],
        repository: DeploymentPresetRepository,
    ) -> None:
        created = await ops.create_global_entity_with_fields(_creator(), _slots(("cpu", "2")))

        await repository.update(DeploymentPresetUpdater(preset_id=created.data.id), [])

        assert await _slot_map(database, created.data.id) == {}


class TestReadAndPurge:
    async def test_get_by_id_round_trip(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[DeploymentRevisionPresetData],
        repository: DeploymentPresetRepository,
    ) -> None:
        created = await ops.create_global_entity_with_fields(_creator("p1"), _slots(("cpu", "1")))

        fetched = await repository.get_by_id(created.data.id)

        assert fetched.id == created.data.id
        assert fetched.name == "p1"

    async def test_purge_takes_the_slots_with_it(
        self,
        database: ExtendedAsyncSAEngine,
        ops: OpsRepository[DeploymentRevisionPresetData],
        repository: DeploymentPresetRepository,
    ) -> None:
        created = await ops.create_global_entity_with_fields(
            _creator(), _slots(("cpu", "1"), ("mem", "8"))
        )

        await ops.purge_entity(DeploymentPresetPurger(created.data.id))

        with pytest.raises(DeploymentRevisionPresetNotFound):
            await repository.get_by_id(created.data.id)
        assert await _slot_map(database, created.data.id) == {}


class TestReadingBackWhatSqlComputed:
    """The rank is computed in the INSERT, so the row is read back once — and only
    then. These pin the round trips, which is the whole cost of the mechanism."""

    async def test_one_create_costs_one_extra_select(
        self, database: ExtendedAsyncSAEngine, ops: OpsRepository[DeploymentRevisionPresetData]
    ) -> None:
        verbs: list[str] = []

        def record(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
            verbs.append(statement.split()[0].upper())

        sa.event.listen(database.sync_engine, "before_cursor_execute", record)
        try:
            await ops.create_global_entity(_creator())
        finally:
            sa.event.remove(database.sync_engine, "before_cursor_execute", record)

        assert verbs.count("SELECT") == 1, verbs

    async def test_each_row_of_a_bulk_create_is_read_back(
        self, database: ExtendedAsyncSAEngine, ops: OpsRepository[DeploymentRevisionPresetData]
    ) -> None:
        verbs: list[str] = []

        def record(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
            verbs.append(statement.split()[0].upper())

        sa.event.listen(database.sync_engine, "before_cursor_execute", record)
        try:
            created = await ops.atomic_create_global_entities([
                _creator("p1"),
                _creator("p2"),
                _creator("p3"),
            ])
        finally:
            sa.event.remove(database.sync_engine, "before_cursor_execute", record)

        assert verbs.count("SELECT") == 3, verbs
        assert sorted(d.rank for d in created) == [RANK_GAP, RANK_GAP * 2, RANK_GAP * 3]
