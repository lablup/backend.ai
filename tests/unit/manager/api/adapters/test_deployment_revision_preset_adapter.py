"""The deployment revision preset DataLoader path: each preset is answered for."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.errors.common import GenericForbidden

READABLE = DeploymentPresetID(uuid4())
DENIED = DeploymentPresetID(uuid4())
ABSENT = DeploymentPresetID(uuid4())


@pytest.fixture
def readable() -> DeploymentRevisionPresetData:
    return DeploymentRevisionPresetData(
        id=READABLE,
        runtime_variant_id=RuntimeVariantID(uuid4()),
        name="preset",
        description=None,
        rank=0,
        image_id=ImageID(uuid4()),
        model_definition=None,
        resource_opts=[],
        cluster_mode="single-node",
        cluster_size=1,
        startup_command=None,
        bootstrap_script=None,
        environ=[],
        runtime_variant_preset_values=[],
        replica_count=1,
        deployment_strategy=DeploymentStrategy.ROLLING,
        deployment_strategy_spec={},
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this preset")


@pytest.fixture
def processors(readable: DeploymentRevisionPresetData, denial: GenericForbidden) -> MagicMock:
    processors = MagicMock()
    processors.bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[DeploymentRevisionPresetData].succeeded(READABLE, readable),
                PartialBulkEntityResult[DeploymentRevisionPresetData].denied(DENIED, denial),
                PartialBulkEntityResult[DeploymentRevisionPresetData].nothing(ABSENT),
            ]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> DeploymentRevisionPresetAdapter:
    return DeploymentRevisionPresetAdapter(processors)


async def test_batch_load_answers_per_id(
    adapter: DeploymentRevisionPresetAdapter,
    denial: GenericForbidden,
) -> None:
    node, refused, missing = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert refused is denial
    assert missing is None


async def test_no_ids_read_nothing(
    adapter: DeploymentRevisionPresetAdapter, processors: MagicMock
) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.bulk_get.run.assert_not_awaited()
