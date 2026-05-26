"""Tests for deployment revision preset create/update with separated resource slots.

Verifies that preset rows and their resource-slot rows are persisted as separate
single-table operations, that the rank is assigned race-free via the next-value op,
and that update replaces / keeps / clears slots correctly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.manager.data.deployment_revision_preset.types import ResourceSlotEntryData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow, ResourceSlotTypeRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables

# Shared runtime variant id; the preset's rank scope and the FOR UPDATE lock target it.
_VARIANT_ID = RuntimeVariantID(uuid4())


def _make_spec(name: str = "preset-1") -> DeploymentRevisionPresetCreatorSpec:
    return DeploymentRevisionPresetCreatorSpec(
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
        preset_values=[],
        replica_count=1,
        deployment_strategy=DeploymentStrategy.ROLLING,
        deployment_strategy_spec={},
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
        [
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
                    default_model_definition=ModelDefinitionDraft(),
                )
            )
            session.add_all([
                ResourceSlotTypeRow(slot_name="cpu", slot_type="count"),
                ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"),
            ])
        yield DeploymentRevisionPresetRepository(DBOpsProvider(database_connection))


class TestCreate:
    async def test_persists_preset_and_slots_separately(
        self, repository: DeploymentRevisionPresetRepository
    ) -> None:
        data = await repository.create(_make_spec(), _slot_specs(("cpu", "2"), ("mem", "1024")))
        slots = await repository.get_resource_slots(data.id)
        assert dict(slots) == {"cpu": Decimal("2"), "mem": Decimal("1024")}

    async def test_create_assigns_increasing_rank(
        self, repository: DeploymentRevisionPresetRepository
    ) -> None:
        first = await repository.create(_make_spec(name="p1"), _slot_specs(("cpu", "1")))
        second = await repository.create(_make_spec(name="p2"), _slot_specs(("cpu", "1")))
        assert second.rank > first.rank


class TestUpdate:
    async def test_replaces_slots(self, repository: DeploymentRevisionPresetRepository) -> None:
        data = await repository.create(_make_spec(), _slot_specs(("cpu", "2")))
        updater = Updater(spec=DeploymentRevisionPresetUpdaterSpec(), pk_value=data.id)

        await repository.update(updater, _slot_specs(("cpu", "4"), ("mem", "512")))

        slots = await repository.get_resource_slots(data.id)
        assert dict(slots) == {"cpu": Decimal("4"), "mem": Decimal("512")}

    async def test_none_keeps_slots_and_updates_preset(
        self, repository: DeploymentRevisionPresetRepository
    ) -> None:
        data = await repository.create(_make_spec(), _slot_specs(("cpu", "2")))
        updater = Updater(
            spec=DeploymentRevisionPresetUpdaterSpec(name=OptionalState.update("renamed")),
            pk_value=data.id,
        )

        result = await repository.update(updater, None)

        assert result.name == "renamed"
        slots = await repository.get_resource_slots(data.id)
        assert dict(slots) == {"cpu": Decimal("2")}

    async def test_empty_clears_slots(self, repository: DeploymentRevisionPresetRepository) -> None:
        data = await repository.create(_make_spec(), _slot_specs(("cpu", "2")))
        updater = Updater(spec=DeploymentRevisionPresetUpdaterSpec(), pk_value=data.id)

        await repository.update(updater, [])

        slots = await repository.get_resource_slots(data.id)
        assert slots == []
