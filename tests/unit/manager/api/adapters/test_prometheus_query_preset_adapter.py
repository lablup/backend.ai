"""The prometheus query preset DataLoader path: each preset is answered for."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.prometheus_query_preset import (
    PrometheusQueryPresetEntityType,
    PrometheusQueryPresetID,
)
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
)
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericForbidden

READABLE = PrometheusQueryPresetID(uuid4())
DENIED = PrometheusQueryPresetID(uuid4())
ABSENT = PrometheusQueryPresetID(uuid4())


@pytest.fixture
def readable() -> PrometheusQueryPresetData:
    return PrometheusQueryPresetData(
        id=READABLE,
        name="cpu-by-kernel",
        description=None,
        rank=0,
        category_id=None,
        metric_name="container_cpu_usage",
        query_template="sum(rate(container_cpu_usage[{time_window}]))",
        time_window=None,
        filter_labels=[],
        group_labels=[],
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this preset")


@pytest.fixture
def processors(readable: PrometheusQueryPresetData, denial: GenericForbidden) -> MagicMock:
    processors = MagicMock()
    processors.bulk_get_presets.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[PrometheusQueryPresetData].succeeded(READABLE, readable),
                PartialBulkEntityResult[PrometheusQueryPresetData].denied(DENIED, denial),
                PartialBulkEntityResult[PrometheusQueryPresetData].failed(
                    ABSENT, EntityNotFoundError(entity_type=PrometheusQueryPresetEntityType())
                ),
            ]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> PrometheusQueryPresetAdapter:
    return PrometheusQueryPresetAdapter(processors)


async def test_batch_load_answers_per_id(
    adapter: PrometheusQueryPresetAdapter, processors: MagicMock, denial: GenericForbidden
) -> None:
    node, refused, missing = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert refused is denial
    assert missing is None
    action = processors.bulk_get_presets.run.await_args.args[0]
    assert list(action.ids) == [READABLE, DENIED, ABSENT]


async def test_no_ids_read_nothing(
    adapter: PrometheusQueryPresetAdapter, processors: MagicMock
) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.bulk_get_presets.run.assert_not_awaited()
