"""The runtime variant preset DataLoader path: each preset is answered for."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import (
    RuntimeVariantPresetEntityType,
    RuntimeVariantPresetID,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.errors.base.entity import EntityNotFoundError

READABLE = RuntimeVariantPresetID(uuid4())
ABSENT = RuntimeVariantPresetID(uuid4())


@pytest.fixture
def readable() -> RuntimeVariantPresetData:
    return RuntimeVariantPresetData(
        id=READABLE,
        runtime_variant_id=RuntimeVariantID(uuid4()),
        name="max-tokens",
        description=None,
        rank=0,
        preset_target=PresetTarget.ARGS,
        value_type=PresetValueType.INT,
        default_value="4096",
        key="--max-tokens",
        required=False,
        added_version=None,
        deprecated_version=None,
        category=None,
        ui_type=None,
        display_name=None,
        ui_option=None,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=None,
    )


@pytest.fixture
def processors(readable: RuntimeVariantPresetData) -> MagicMock:
    processors = MagicMock()
    processors.public_bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[RuntimeVariantPresetData].succeeded(READABLE, readable),
                PartialBulkEntityResult[RuntimeVariantPresetData].failed(
                    ABSENT, EntityNotFoundError(entity_type=RuntimeVariantPresetEntityType())
                ),
            ]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> RuntimeVariantPresetAdapter:
    return RuntimeVariantPresetAdapter(processors)


async def test_batch_load_answers_per_id(
    adapter: RuntimeVariantPresetAdapter, processors: MagicMock
) -> None:
    node, missing = await adapter.batch_load_by_ids([READABLE, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert missing is None
    action = processors.public_bulk_get.run.await_args.args[0]
    assert list(action.ids) == [READABLE, ABSENT]


async def test_no_ids_read_nothing(
    adapter: RuntimeVariantPresetAdapter, processors: MagicMock
) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.public_bulk_get.run.assert_not_awaited()
