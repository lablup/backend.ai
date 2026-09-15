"""The Reservoir registry DataLoader path: each registry is answered for."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.reservoir_registry.adapter import ReservoirRegistryAdapter
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryConnectionData
from ai.backend.manager.errors.common import GenericForbidden

READABLE = ArtifactRegistryID(uuid4())
DENIED = ArtifactRegistryID(uuid4())
ABSENT = ArtifactRegistryID(uuid4())


@pytest.fixture
def connection() -> ReservoirRegistryConnectionData:
    return ReservoirRegistryConnectionData(
        id=READABLE,
        endpoint="https://reservoir.test.local",
        access_key="access",
        secret_key="secret",
        api_version="v1",
    )


@pytest.fixture
def meta() -> ArtifactRegistryData:
    return ArtifactRegistryData(
        id=ArtifactRegistryID(uuid4()),
        registry_id=READABLE,
        name="reservoir",
        type=ArtifactRegistryType.RESERVOIR,
    )


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this registry")


@pytest.fixture
def processors(
    connection: ReservoirRegistryConnectionData,
    meta: ArtifactRegistryData,
    denial: GenericForbidden,
) -> MagicMock:
    processors = MagicMock()
    processors.bulk_get_reservoir_registries.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[ReservoirRegistryConnectionData].succeeded(
                    READABLE, connection
                ),
                PartialBulkEntityResult[ReservoirRegistryConnectionData].denied(DENIED, denial),
                PartialBulkEntityResult[ReservoirRegistryConnectionData].nothing(ABSENT),
            ]
        )
    )
    processors.get_registry_metas.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[PartialBulkEntityResult[ArtifactRegistryData].succeeded(READABLE, meta)]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ReservoirRegistryAdapter:
    return ReservoirRegistryAdapter(processors)


async def test_batch_load_answers_per_id(
    adapter: ReservoirRegistryAdapter,
    denial: GenericForbidden,
) -> None:
    node, refused, missing = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert node.name == "reservoir"
    assert refused is denial
    assert missing is None


async def test_no_ids_read_nothing(
    adapter: ReservoirRegistryAdapter, processors: MagicMock
) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.bulk_get_reservoir_registries.run.assert_not_awaited()
    processors.get_registry_metas.run.assert_not_awaited()
