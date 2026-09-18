"""Cursor and offset pagination of the service catalog adapter's search."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
)
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.service_catalog.adapter import ServiceCatalogAdapter
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.models.service_catalog.row import (
    ServiceCatalogEndpointRow,
    ServiceCatalogRow,
)
from ai.backend.manager.models.service_catalog.upserters import ServiceCatalogUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.service_catalog.repository import ServiceCatalogRepository
from ai.backend.manager.services.service_catalog.actions.search import (
    SearchServiceCatalogsAction,
)
from ai.backend.testutils.db import with_tables

type _PageFetch = Callable[[str | None], Awaitable[tuple[list[uuid.UUID], bool]]]

_PAGE_SIZE = 2

_NEWER = datetime(2026, 2, 1, tzinfo=UTC)
_OLDER = datetime(2026, 1, 1, tzinfo=UTC)


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


class TestServiceCatalogPagination:
    @pytest.fixture
    async def database(
        self, global_entity_ids: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            global_entity_ids,
            [
                ServiceCatalogRow,
                ServiceCatalogEndpointRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
            ],
        ):
            yield global_entity_ids

    @pytest.fixture
    async def ordered_ids(self, database: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
        """Six services, three sharing each registered_at.

        Forward order is registered_at DESC, then id ASC.
        """
        repository = ServiceCatalogRepository(V2DBOpsProvider(database))
        rows: list[tuple[datetime, uuid.UUID]] = []
        for index in range(6):
            service_id = await repository.register(
                ServiceCatalogUpserter(
                    service_group="manager",
                    instance_id=f"mgr-{index}",
                    display_name=f"Manager {index}",
                    version="1",
                    labels={},
                    startup_time=_OLDER,
                    config_hash="abc",
                ),
                [],
            )
            registered_at = _NEWER if index % 2 else _OLDER
            async with database.begin_session() as db_sess:
                await db_sess.execute(
                    sa.update(ServiceCatalogRow)
                    .where(ServiceCatalogRow.id == service_id)
                    .values(registered_at=registered_at)
                )
            rows.append((registered_at, service_id))
        newer = sorted(row_id for at, row_id in rows if at == _NEWER)
        older = sorted(row_id for at, row_id in rows if at == _OLDER)
        return newer + older

    @pytest.fixture
    def adapter(self, database: ExtendedAsyncSAEngine) -> ServiceCatalogAdapter:
        repository: OpsRepository[object] = OpsRepository(V2DBOpsProvider(database))

        async def run(action: SearchServiceCatalogsAction) -> object:
            return await repository.search_in_global(action.searcher)

        processors = MagicMock()
        processors.global_search_service_catalogs.run = run
        return ServiceCatalogAdapter(processors)

    async def test_forward_pages_visit_every_row_once(
        self, adapter: ServiceCatalogAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.admin_search(
                AdminSearchServiceCatalogsInput(first=_PAGE_SIZE, after=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_next_page

        assert await _walk(fetch) == ordered_ids

    async def test_backward_pages_visit_every_row_once_in_reverse(
        self, adapter: ServiceCatalogAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.admin_search(
                AdminSearchServiceCatalogsInput(last=_PAGE_SIZE, before=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_previous_page

        assert await _walk(fetch) == list(reversed(ordered_ids))

    async def test_offset_page_follows_forward_order(
        self, adapter: ServiceCatalogAdapter, ordered_ids: list[uuid.UUID]
    ) -> None:
        payload = await adapter.admin_search(AdminSearchServiceCatalogsInput(limit=2, offset=2))

        assert [item.entity_id for item in payload.items] == ordered_ids[2:4]
        assert payload.total_count == len(ordered_ids)

    async def test_mixing_cursor_and_offset_is_rejected(
        self, adapter: ServiceCatalogAdapter
    ) -> None:
        with pytest.raises(InvalidGraphQLParameters):
            await adapter.admin_search(AdminSearchServiceCatalogsInput(first=2, limit=2))
