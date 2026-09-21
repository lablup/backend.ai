"""The resource group usage read: the name resolves to the group, which the read is
answered for."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.actions.v2.ops.result import LookupOpsResult
from ai.backend.manager.api.adapters.resource_allocation.adapter import ResourceAllocationAdapter
from ai.backend.manager.data.resource_allocation.types import ResourceGroupUsageData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.services.session.resource_allocation.actions.get_resource_group_usage import (
    GetResourceGroupUsageActionResult,
)

READABLE = ResourceGroupName("rg-readable")
READABLE_ID = ResourceGroupID(uuid.uuid4())


@pytest.fixture
def usage() -> ResourceGroupUsageData:
    return ResourceGroupUsageData(
        capacity=[SlotQuantity(slot_name="cpu", quantity=Decimal(8))],
        used=[SlotQuantity(slot_name="cpu", quantity=Decimal(2))],
        free=[SlotQuantity(slot_name="cpu", quantity=Decimal(6))],
        max_per_node=[SlotQuantity(slot_name="cpu", quantity=Decimal(4))],
    )


@pytest.fixture
def denial() -> NotEnoughPermission:
    return NotEnoughPermission("no read on this resource group")


@pytest.fixture
def processors(usage: ResourceGroupUsageData) -> MagicMock:
    processors = MagicMock()
    processors.resource_group.lookup.run = AsyncMock(
        return_value=LookupOpsResult(resolved_entity_id=READABLE_ID)
    )
    processors.session.resource_allocation.get_resource_group_usage.run = AsyncMock(
        return_value=GetResourceGroupUsageActionResult(usage=usage)
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ResourceAllocationAdapter:
    return ResourceAllocationAdapter(
        processors.session,
        processors.domain,
        processors.user,
        processors.resource_group,
        config_provider=None,
    )


async def test_usage_is_read_on_the_group_the_name_resolves_to(
    adapter: ResourceAllocationAdapter,
    processors: MagicMock,
) -> None:
    payload = await adapter.resource_group_usage(rg_name=str(READABLE))

    lookup_action = processors.resource_group.lookup.run.await_args.args[0]
    assert lookup_action.name == READABLE
    usage_action = (
        processors.session.resource_allocation.get_resource_group_usage.run.await_args.args[0]
    )
    assert usage_action.entity_id() == READABLE_ID
    assert usage_action.rg_name == READABLE
    assert payload.resource_group.capacity[0].quantity == Decimal(8)
    assert payload.resource_group.used[0].quantity == Decimal(2)
    assert payload.resource_group.free[0].quantity == Decimal(6)
    assert payload.resource_group.max_per_node[0].quantity == Decimal(4)


async def test_a_group_the_caller_may_not_read_is_refused(
    adapter: ResourceAllocationAdapter,
    processors: MagicMock,
    denial: NotEnoughPermission,
) -> None:
    processors.session.resource_allocation.get_resource_group_usage.run = AsyncMock(
        side_effect=denial
    )

    with pytest.raises(NotEnoughPermission):
        await adapter.resource_group_usage(rg_name=str(READABLE))


async def test_a_name_matching_no_group_ends_at_the_lookup(
    adapter: ResourceAllocationAdapter,
    processors: MagicMock,
) -> None:
    processors.resource_group.lookup.run = AsyncMock(
        side_effect=EntityNotFoundError(entity_type=ResourceGroupEntityType())
    )

    with pytest.raises(EntityNotFoundError):
        await adapter.resource_group_usage(rg_name="rg-absent")
    processors.session.resource_allocation.get_resource_group_usage.run.assert_not_awaited()
