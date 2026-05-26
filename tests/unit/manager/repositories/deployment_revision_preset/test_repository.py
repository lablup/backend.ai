"""Tests for deployment revision preset create/update with separated resource slots.

Verifies that preset rows and their resource-slot rows are persisted as separate
single-table operations, and that update replaces / keeps / clears slots correctly
(the latter exercising the previously-broken resource-slot update path).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.manager.data.deployment_revision_preset.types import ResourceSlotEntryData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow, ResourceSlotTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment_revision_preset.creators import (
    DeploymentRevisionPresetCreatorSpec,
    PresetResourceSlotDependentCreatorSpec,
)
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)
from ai.backend.manager.repositories.deployment_revision_preset.updaters import (
    DeploymentRevisionPresetUpdaterSpec,
)
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


def _make_creator(name: str = "preset-1") -> Creator[DeploymentRevisionPresetRow]:
    return Creator(
        spec=DeploymentRevisionPresetCreatorSpec(
            runtime_variant_id=RuntimeVariantID(uuid4()),
            name=name,
            description=None,
            rank=0,
            image_id=ImageID(uuid4()),
            model_definition=None,
            resource_opts=[],
            cluster_mode="single-node",
            cluster_size=1,
            startup_command=None,
            bootstrap_script=None,
            environ={},
            preset_values=[],
            replica_count=1,
            deployment_strategy=DeploymentStrategy.ROLLING,
            deployment_strategy_spec={},
        )
    )


def _slot_specs(*entries: tuple[str, str]) -> list[PresetResourceSlotDependentCreatorSpec]:
    return [
        PresetResourceSlotDependentCreatorSpec(
            entry=ResourceSlotEntryData(resource_type=name, quantity=quantity)
        )
        for name, quantity in entries
    ]


@pytest.fixture
async def repository(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[DeploymentRevisionPresetRepository, None]:
    async with with_tables(
        database_connection,
        [ResourceSlotTypeRow, DeploymentRevisionPresetRow, PresetResourceSlotRow],
    ):
        async with database_connection.begin_session() as session:
            session.add_all([
                ResourceSlotTypeRow(slot_name="cpu", slot_type="count"),
                ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"),
            ])
        yield DeploymentRevisionPresetRepository(database_connection)


class TestCreate:
    async def test_persists_preset_and_slots_separately(
        self, repository: DeploymentRevisionPresetRepository
    ) -> None:
        data = await repository.create(_make_creator(), _slot_specs(("cpu", "2"), ("mem", "1024")))
        slots = await repository.get_resource_slots(data.id)
        assert dict(slots) == {"cpu": Decimal("2"), "mem": Decimal("1024")}


class TestUpdate:
    async def test_replaces_slots(self, repository: DeploymentRevisionPresetRepository) -> None:
        data = await repository.create(_make_creator(), _slot_specs(("cpu", "2")))
        updater = Updater(spec=DeploymentRevisionPresetUpdaterSpec(), pk_value=data.id)

        await repository.update(updater, _slot_specs(("cpu", "4"), ("mem", "512")))

        slots = await repository.get_resource_slots(data.id)
        assert dict(slots) == {"cpu": Decimal("4"), "mem": Decimal("512")}

    async def test_none_keeps_slots_and_updates_preset(
        self, repository: DeploymentRevisionPresetRepository
    ) -> None:
        data = await repository.create(_make_creator(), _slot_specs(("cpu", "2")))
        updater = Updater(
            spec=DeploymentRevisionPresetUpdaterSpec(name=OptionalState.update("renamed")),
            pk_value=data.id,
        )

        result = await repository.update(updater, None)

        assert result.name == "renamed"
        slots = await repository.get_resource_slots(data.id)
        assert dict(slots) == {"cpu": Decimal("2")}

    async def test_empty_clears_slots(self, repository: DeploymentRevisionPresetRepository) -> None:
        data = await repository.create(_make_creator(), _slot_specs(("cpu", "2")))
        updater = Updater(spec=DeploymentRevisionPresetUpdaterSpec(), pk_value=data.id)

        await repository.update(updater, [])

        slots = await repository.get_resource_slots(data.id)
        assert slots == []
