from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.services.scaling_group.actions.resolve_resource_group_id_by_name import (
    ResolveResourceGroupIDByNameActionResult,
)

_RESOURCE_GROUP_ID = ResourceGroupID(UUID("550e8400-e29b-41d4-a716-446655440000"))


@pytest.fixture
def processors() -> MagicMock:
    processors = MagicMock()
    processors.scaling_group.resolve_resource_group_id_by_name.wait_for_complete = AsyncMock(
        return_value=ResolveResourceGroupIDByNameActionResult(resource_group_id=_RESOURCE_GROUP_ID)
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> FairShareAdapter:
    return FairShareAdapter(processors)


class TestResourceGroupIdentifierResolution:
    async def test_id_is_used_without_name_to_id_resolution(
        self, adapter: FairShareAdapter, processors: MagicMock
    ) -> None:
        result = await adapter.resolve_resource_group_id(_RESOURCE_GROUP_ID, None)

        assert result == _RESOURCE_GROUP_ID
        processors.scaling_group.resolve_resource_group_id_by_name.wait_for_complete.assert_not_awaited()

    async def test_deprecated_name_is_resolved_to_id(
        self, adapter: FairShareAdapter, processors: MagicMock
    ) -> None:
        result = await adapter.resolve_resource_group_id(None, "default")

        assert result == _RESOURCE_GROUP_ID
        processors.scaling_group.resolve_resource_group_id_by_name.wait_for_complete.assert_awaited_once()

    async def test_id_takes_precedence_when_both_are_provided(
        self, adapter: FairShareAdapter, processors: MagicMock
    ) -> None:
        result = await adapter.resolve_resource_group_id(_RESOURCE_GROUP_ID, "stale-name")

        assert result == _RESOURCE_GROUP_ID
        processors.scaling_group.resolve_resource_group_id_by_name.wait_for_complete.assert_not_awaited()

    async def test_missing_identifier_is_rejected(self, adapter: FairShareAdapter) -> None:
        with pytest.raises(InvalidAPIParameters):
            await adapter.resolve_resource_group_id(None, None)
