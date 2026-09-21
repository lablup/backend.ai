"""Cursor and offset pagination of the resource slot adapter's three searches."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_allocation import ResourceAllocationID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
)
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.ops.service import GlobalSearcherService
from ai.backend.manager.services.resource_slot.actions.scoped_search_resource_slot_types import (
    ScopedSearchResourceSlotTypesAction,
)
from ai.backend.testutils.db import with_tables

type _PageFetch = Callable[[str | None], Awaitable[tuple[list[uuid.UUID], bool]]]

_PAGE_SIZE = 2

_SLOT_NAMES = ("cpu", "mem")
_OWNER_COUNT = 3


async def _walk(fetch: _PageFetch) -> list[uuid.UUID]:
    """Follow the last id of each page as the next cursor until no page is left."""
    visited: list[uuid.UUID] = []
    cursor: str | None = None
    while True:
        ids, has_more = await fetch(cursor)
        assert len(ids) <= _PAGE_SIZE
        visited.extend(ids)
        if not has_more:
            return visited
        cursor = encode_cursor(ids[-1])


async def _seed_slot_types(db: ExtendedAsyncSAEngine) -> None:
    async with db.begin_session() as db_sess:
        for name in _SLOT_NAMES:
            db_sess.add(ResourceSlotTypeRow(slot_name=name, slot_type="count", rank=0))


class TestSlotTypePagination:
    @pytest.fixture
    async def database(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [ResourceSlotTypeRow]):
            yield database_connection

    @pytest.fixture
    async def ordered_ids(self, database: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
        """Five slot types in forward order (slot_name ASC)."""
        names = ["cpu", "cuda.device", "cuda.shares", "mem", "rocm.device"]
        ids = {name: ResourceSlotTypeUUID(uuid.uuid4()) for name in names}
        async with database.begin_session() as db_sess:
            for name in reversed(names):
                db_sess.add(
                    ResourceSlotTypeRow(uuid=ids[name], slot_name=name, slot_type="count", rank=0)
                )
        return [ids[name] for name in names]

    @pytest.fixture
    def adapter(self, database: ExtendedAsyncSAEngine) -> ResourceSlotAdapter:
        repository: OpsRepository[ResourceSlotTypeData] = OpsRepository(V2DBOpsProvider(database))

        async def run(action: ScopedSearchResourceSlotTypesAction) -> object:
            return await repository.scoped_search(action.searcher)

        processors = MagicMock()
        processors.scoped_search_resource_slot_types.run = run
        return ResourceSlotAdapter(resource_slot=processors, agent=MagicMock(), domain=MagicMock())

    async def test_forward_pages_visit_every_row_once(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_slot_types(
                AdminSearchResourceSlotTypesInput(first=_PAGE_SIZE, after=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_next_page

        assert await _walk(fetch) == ordered_ids

    async def test_backward_pages_visit_every_row_once_in_reverse(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_slot_types(
                AdminSearchResourceSlotTypesInput(last=_PAGE_SIZE, before=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_previous_page

        assert await _walk(fetch) == list(reversed(ordered_ids))

    async def test_offset_page_follows_forward_order(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        payload = await adapter.search_slot_types(
            AdminSearchResourceSlotTypesInput(limit=2, offset=2)
        )

        assert [item.entity_id for item in payload.items] == ordered_ids[2:4]
        assert payload.total_count == len(ordered_ids)

    async def test_mixing_cursor_and_offset_is_rejected(self, adapter: ResourceSlotAdapter) -> None:
        with pytest.raises(InvalidGraphQLParameters):
            await adapter.search_slot_types(AdminSearchResourceSlotTypesInput(first=2, limit=2))


class TestAgentResourcePagination:
    @pytest.fixture
    async def database(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [ResourceGroupRow, AgentRow, ResourceSlotTypeRow, AgentResourceRow],
        ):
            yield database_connection

    @pytest.fixture
    async def ordered_ids(self, database: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
        """Every agent carries every slot, so each slot_name is shared by several rows.

        Forward order is slot_name ASC, then id ASC.
        """
        await _seed_slot_types(database)
        resource_group_id = ResourceGroupID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name="default",
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
        rows: list[tuple[str, uuid.UUID]] = []
        async with database.begin_session() as db_sess:
            for index in range(_OWNER_COUNT):
                agent_id = f"i-agent-{index}"
                agent_uuid = AgentUUID(uuid.uuid4())
                db_sess.add(
                    AgentRow(
                        uuid=agent_uuid,
                        id=agent_id,
                        status=AgentStatus.ALIVE,
                        status_changed=datetime.now(tzutc()),
                        region="test-region",
                        scaling_group="default",
                        resource_group_id=resource_group_id,
                        addr=f"tcp://127.0.0.1:{6001 + index}",
                        version="24.12.0",
                        architecture="x86_64",
                        compute_plugins={},
                    )
                )
                await db_sess.flush()
                for slot_name in _SLOT_NAMES:
                    row_id = AgentResourceID(uuid.uuid4())
                    db_sess.add(
                        AgentResourceRow(
                            id=row_id,
                            agent_id=agent_id,
                            agent_uuid=agent_uuid,
                            slot_name=slot_name,
                            capacity=Decimal("8"),
                            used=Decimal("0"),
                        )
                    )
                    rows.append((slot_name, row_id))
        return [row_id for _, row_id in sorted(rows)]

    @pytest.fixture
    def adapter(self, database: ExtendedAsyncSAEngine) -> ResourceSlotAdapter:
        repository: OpsRepository[AgentResourceData] = OpsRepository(V2DBOpsProvider(database))
        processors = MagicMock()
        processors.search_agent_resources.run = GlobalSearcherService(repository).execute
        return ResourceSlotAdapter(resource_slot=processors, agent=MagicMock(), domain=MagicMock())

    async def test_forward_pages_visit_every_row_once(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_agent_resources(
                AdminSearchAgentResourcesInput(first=_PAGE_SIZE, after=cursor)
            )
            return [item.field_id for item in payload.items], payload.has_next_page

        assert await _walk(fetch) == ordered_ids

    async def test_backward_pages_visit_every_row_once_in_reverse(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_agent_resources(
                AdminSearchAgentResourcesInput(last=_PAGE_SIZE, before=cursor)
            )
            return [item.field_id for item in payload.items], payload.has_previous_page

        assert await _walk(fetch) == list(reversed(ordered_ids))

    async def test_offset_page_follows_forward_order(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        payload = await adapter.search_agent_resources(
            AdminSearchAgentResourcesInput(limit=2, offset=2)
        )

        assert [item.field_id for item in payload.items] == ordered_ids[2:4]
        assert payload.total_count == len(ordered_ids)

    async def test_mixing_cursor_and_offset_is_rejected(self, adapter: ResourceSlotAdapter) -> None:
        with pytest.raises(InvalidGraphQLParameters):
            await adapter.search_agent_resources(AdminSearchAgentResourcesInput(last=2, offset=0))


class TestResourceAllocationPagination:
    @pytest.fixture
    async def database(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def ordered_ids(self, database: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
        """Every kernel is allocated every slot, so each slot_name is shared by several rows.

        Forward order is slot_name ASC, then id ASC.
        """
        await _seed_slot_types(database)
        domain_id = DomainID(uuid.uuid4())
        resource_group_id = ResourceGroupID(uuid.uuid4())
        project_id = uuid.uuid4()
        async with database.begin_session() as db_sess:
            db_sess.add(DomainRow(id=domain_id, name="default"))
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=0,
                    max_network_count=5,
                )
            )
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name="default",
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            await db_sess.flush()
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name="default",
                    domain_name="default",
                    resource_policy="default",
                )
            )
            db_sess.add(
                AgentRow(
                    id="i-agent",
                    status=AgentStatus.ALIVE,
                    status_changed=datetime.now(tzutc()),
                    region="test-region",
                    scaling_group="default",
                    resource_group_id=resource_group_id,
                    addr="tcp://127.0.0.1:6001",
                    version="24.12.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
        rows: list[tuple[str, uuid.UUID]] = []
        async with database.begin_session() as db_sess:
            for _ in range(_OWNER_COUNT):
                session_id = uuid.uuid4()
                kernel_id = uuid.uuid4()
                db_sess.add(
                    SessionRow(
                        id=session_id,
                        domain_id=domain_id,
                        domain_name="default",
                        group_id=project_id,
                        resource_group_id=resource_group_id,
                        scaling_group_name="default",
                        user_uuid=uuid.uuid4(),
                    )
                )
                await db_sess.flush()
                db_sess.add(
                    KernelRow(
                        id=kernel_id,
                        session_id=session_id,
                        domain_name="default",
                        group_id=project_id,
                        user_uuid=uuid.uuid4(),
                        status=KernelStatus.RUNNING,
                        repl_in_port=0,
                        repl_out_port=0,
                        stdin_port=0,
                        stdout_port=0,
                        scaling_group="default",
                        resource_group_id=resource_group_id,
                        agent="i-agent",
                    )
                )
                await db_sess.flush()
                for slot_name in _SLOT_NAMES:
                    row_id = ResourceAllocationID(uuid.uuid4())
                    db_sess.add(
                        ResourceAllocationRow(
                            id=row_id,
                            kernel_id=kernel_id,
                            slot_name=slot_name,
                            requested=Decimal("1"),
                        )
                    )
                    rows.append((slot_name, row_id))
        return [row_id for _, row_id in sorted(rows)]

    @pytest.fixture
    def adapter(self, database: ExtendedAsyncSAEngine) -> ResourceSlotAdapter:
        repository: OpsRepository[ResourceAllocationData] = OpsRepository(V2DBOpsProvider(database))
        processors = MagicMock()
        processors.search_resource_allocations.run = GlobalSearcherService(repository).execute
        return ResourceSlotAdapter(resource_slot=processors, agent=MagicMock(), domain=MagicMock())

    async def test_forward_pages_visit_every_row_once(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_allocations(
                AdminSearchResourceAllocationsInput(first=_PAGE_SIZE, after=cursor)
            )
            return [item.field_id for item in payload.items], payload.has_next_page

        assert await _walk(fetch) == ordered_ids

    async def test_backward_pages_visit_every_row_once_in_reverse(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_allocations(
                AdminSearchResourceAllocationsInput(last=_PAGE_SIZE, before=cursor)
            )
            return [item.field_id for item in payload.items], payload.has_previous_page

        assert await _walk(fetch) == list(reversed(ordered_ids))

    async def test_offset_page_follows_forward_order(
        self, adapter: ResourceSlotAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        payload = await adapter.search_allocations(
            AdminSearchResourceAllocationsInput(limit=2, offset=2)
        )

        assert [item.field_id for item in payload.items] == ordered_ids[2:4]
        assert payload.total_count == len(ordered_ids)

    async def test_mixing_cursor_and_offset_is_rejected(self, adapter: ResourceSlotAdapter) -> None:
        with pytest.raises(InvalidGraphQLParameters):
            await adapter.search_allocations(AdminSearchResourceAllocationsInput(first=2, offset=0))
