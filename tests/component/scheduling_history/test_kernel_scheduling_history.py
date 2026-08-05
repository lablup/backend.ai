"""Component tests for the kernel scheduling-history v2 SDK client.

Drives ``V2SchedulingHistoryClient`` against a real aiohttp server and DB, covering
routing, the auth middleware on each route, and request/response serialization for:

- ``POST /v2/scheduling-history/kernels/admin/search`` (superadmin)
- ``POST /v2/scheduling-history/kernels/scoped/search`` (authenticated, RBAC-scoped)

Filter and ordering semantics are verified in ``tests/unit``; what matters here is that
they survive the round trip through the HTTP boundary.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchKernelHistoriesInput,
    KernelHistoryFilter,
    KernelHistoryOrder,
    ScopedSearchKernelHistoriesInput,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    SearchKernelHistoriesPayload,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    KernelHistoryOrderField,
    KernelHistoryScopeDTO,
    OrderDirection,
)

if TYPE_CHECKING:
    from tests.component.scheduling_history.conftest import KernelHistorySeed


class TestAdminSearchKernelHistories:
    """``/kernels/admin/search`` — superadmin, unscoped."""

    async def test_admin_search_without_filter_returns_all_seeded_kernel_histories(
        self,
        admin_v2_registry: V2ClientRegistry,
        kernel_history_seed: KernelHistorySeed,
    ) -> None:
        """No filter on the unscoped admin route returns every seeded row across all kernels.

        The seed spans two kernels (three rows on one, one on the other); an unfiltered
        admin search must surface all of them, so both id sets are asserted present.
        """
        result = await admin_v2_registry.scheduling_history.search_kernel_history(
            AdminSearchKernelHistoriesInput()
        )

        assert isinstance(result, SearchKernelHistoriesPayload)
        found = {item.id for item in result.items}
        # Subset, not equality: the admin route is global, so unrelated rows may coexist.
        assert set(kernel_history_seed.history_ids) <= found
        assert kernel_history_seed.other_history_id in found

    async def test_admin_search_with_phase_filter_returns_only_matching_rows(
        self,
        admin_v2_registry: V2ClientRegistry,
        kernel_history_seed: KernelHistorySeed,
    ) -> None:
        """A phase filter on the unscoped admin route narrows the result to matching rows only.

        The admin route carries no scope, so callers narrow by filter; a ``phase == RUNNING``
        filter must leave only RUNNING rows of the seeded kernel.
        """
        result = await admin_v2_registry.scheduling_history.search_kernel_history(
            AdminSearchKernelHistoriesInput(
                filter=KernelHistoryFilter(phase=StringFilter(equals="RUNNING")),
            )
        )

        returned = [
            item for item in result.items if item.kernel_id == kernel_history_seed.kernel_id
        ]
        assert returned
        assert {item.phase for item in returned} == {"RUNNING"}


class TestScopedSearchKernelHistories:
    """``/kernels/scoped/search`` — the scope travels in the request body."""

    async def test_scoped_search_returns_only_the_scoped_kernels_histories(
        self,
        admin_v2_registry: V2ClientRegistry,
        kernel_history_seed: KernelHistorySeed,
    ) -> None:
        """A kernel-scoped search returns exactly that kernel's rows and excludes other kernels'.

        Scoping to the seeded kernel must yield its three rows precisely and drop the
        sibling kernel's row, so equality (not subset) and the exclusion are both asserted.
        """
        result = await admin_v2_registry.scheduling_history.kernel_scoped_search(
            ScopedSearchKernelHistoriesInput(
                scope=KernelHistoryScopeDTO(
                    kernel=[UUIDScope(value=kernel_history_seed.kernel_id)]
                ),
            )
        )

        assert isinstance(result, SearchKernelHistoriesPayload)
        assert result.total_count == len(kernel_history_seed.history_ids)
        assert {item.id for item in result.items} == set(kernel_history_seed.history_ids)
        assert kernel_history_seed.other_history_id not in {item.id for item in result.items}

    async def test_scoped_search_with_unknown_kernel_returns_not_found(
        self,
        admin_v2_registry: V2ClientRegistry,
        kernel_history_seed: KernelHistorySeed,
    ) -> None:
        """Scoping to a non-existent kernel fails the existence check and surfaces as a 404.

        The scoped route runs an existence check against ``kernels`` before querying history,
        so a random kernel id must raise ``NotFoundError`` rather than return an empty page.
        """
        with pytest.raises(NotFoundError):
            await admin_v2_registry.scheduling_history.kernel_scoped_search(
                ScopedSearchKernelHistoriesInput(
                    scope=KernelHistoryScopeDTO(kernel=[UUIDScope(value=uuid.uuid4())]),
                )
            )

    async def test_scoped_search_orders_by_attempts_ascending(
        self,
        admin_v2_registry: V2ClientRegistry,
        kernel_history_seed: KernelHistorySeed,
    ) -> None:
        """An ``attempts`` ascending order round-trips through the HTTP boundary.

        The seed staggers ``attempts`` as 1, 2, 3; requesting ASC order must return the
        rows in exactly that sequence.
        """
        result = await admin_v2_registry.scheduling_history.kernel_scoped_search(
            ScopedSearchKernelHistoriesInput(
                scope=KernelHistoryScopeDTO(
                    kernel=[UUIDScope(value=kernel_history_seed.kernel_id)]
                ),
                order=[
                    KernelHistoryOrder(
                        field=KernelHistoryOrderField.ATTEMPTS,
                        direction=OrderDirection.ASC,
                    )
                ],
            )
        )

        assert [item.attempts for item in result.items] == [1, 2, 3]

    async def test_scoped_search_applies_limit_offset_pagination(
        self,
        admin_v2_registry: V2ClientRegistry,
        kernel_history_seed: KernelHistorySeed,
    ) -> None:
        """``limit``/``offset`` shift the page while ``total_count`` stays the full size.

        With three seeded rows ordered by ``attempts`` (1, 2, 3), ``limit=2, offset=1`` skips
        the first row and returns the second and third; a non-zero offset makes the test fail
        if the field is dropped. ``total_count`` still reports all three.
        """
        result = await admin_v2_registry.scheduling_history.kernel_scoped_search(
            ScopedSearchKernelHistoriesInput(
                scope=KernelHistoryScopeDTO(
                    kernel=[UUIDScope(value=kernel_history_seed.kernel_id)]
                ),
                order=[
                    KernelHistoryOrder(
                        field=KernelHistoryOrderField.ATTEMPTS,
                        direction=OrderDirection.ASC,
                    )
                ],
                limit=2,
                offset=1,
            )
        )

        assert [item.attempts for item in result.items] == [2, 3]
        assert result.total_count == len(kernel_history_seed.history_ids)

    async def test_scoped_search_applies_cursor_pagination(
        self,
        admin_v2_registry: V2ClientRegistry,
        kernel_history_seed: KernelHistorySeed,
    ) -> None:
        """``first`` cursor pagination returns a first page and reports a next page exists.

        With three seeded rows, ``first=2`` returns two items and ``has_next_page`` is True.
        """
        result = await admin_v2_registry.scheduling_history.kernel_scoped_search(
            ScopedSearchKernelHistoriesInput(
                scope=KernelHistoryScopeDTO(
                    kernel=[UUIDScope(value=kernel_history_seed.kernel_id)]
                ),
                first=2,
            )
        )

        assert len(result.items) == 2
        assert result.has_next_page is True
