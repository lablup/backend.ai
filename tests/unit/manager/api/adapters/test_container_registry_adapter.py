"""The container registry DataLoader path: each registry is answered for."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.common import GenericForbidden

READABLE = ContainerRegistryID(uuid4())
DENIED = ContainerRegistryID(uuid4())
ABSENT = ContainerRegistryID(uuid4())


@pytest.fixture
def readable() -> ContainerRegistryData:
    return ContainerRegistryData(
        id=READABLE,
        url="https://registry.test.local",
        registry_name="registry.test.local",
        type=ContainerRegistryType.DOCKER,
        project="test",
        username=None,
        password=None,
        ssl_verify=True,
        is_global=True,
        extra=None,
    )


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this registry")


@pytest.fixture
def processors(readable: ContainerRegistryData, denial: GenericForbidden) -> MagicMock:
    processors = MagicMock()
    processors.bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[ContainerRegistryData].succeeded(READABLE, readable),
                PartialBulkEntityResult[ContainerRegistryData].denied(DENIED, denial),
                PartialBulkEntityResult[ContainerRegistryData].nothing(ABSENT),
            ]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ContainerRegistryAdapter:
    return ContainerRegistryAdapter(processors, MagicMock())


async def test_batch_load_answers_per_id(
    adapter: ContainerRegistryAdapter,
    denial: GenericForbidden,
) -> None:
    node, refused, missing = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert refused is denial
    assert missing is None


async def test_no_ids_read_nothing(
    adapter: ContainerRegistryAdapter, processors: MagicMock
) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.bulk_get.run.assert_not_awaited()
