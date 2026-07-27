"""Component tests for the replica-group scheduling-history v2 SDK client.

Drives ``V2SchedulingHistoryClient`` against a real aiohttp server and DB, covering
routing, the auth middleware on each route, and request/response serialization for:

- ``POST /v2/scheduling-history/replica-groups/admin/search`` (superadmin)
- ``POST /v2/scheduling-history/replica-groups/scoped/search`` (authenticated, RBAC-scoped)

A replica group is not an RBAC scope of its own, so the scoped route is scoped by the
owning deployment. Filter and ordering semantics are verified in ``tests/unit``; what
matters here is that they survive the round trip through the HTTP boundary.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchReplicaGroupHistoriesInput,
    ReplicaGroupHistoryFilter,
    ReplicaGroupHistoryOrder,
    ScopedSearchReplicaGroupHistoriesInput,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    SearchReplicaGroupHistoriesPayload,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection,
    ReplicaGroupHistoryCategoryType,
    ReplicaGroupHistoryOrderField,
    ReplicaGroupHistoryScopeDTO,
)
from ai.backend.common.identifier.deployment import DeploymentID

if TYPE_CHECKING:
    from tests.component.scheduling_history.conftest import ReplicaGroupHistorySeed


class TestAdminSearchReplicaGroupHistories:
    """``/replica-groups/admin/search`` — superadmin, unscoped."""

    async def test_admin_search_without_filter_returns_all_seeded_replica_group_histories(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """No filter on the unscoped admin route returns every seeded row across all groups.

        The seed spans two replica groups (four rows on one, one on the other); an
        unfiltered admin search must surface all of them, so both id sets are asserted
        present.
        """
        result = await admin_v2_registry.scheduling_history.search_replica_group_history(
            AdminSearchReplicaGroupHistoriesInput()
        )

        assert isinstance(result, SearchReplicaGroupHistoriesPayload)
        found = {item.id for item in result.items}
        # Subset, not equality: the admin route is global, so unrelated rows may coexist.
        assert set(replica_group_history_seed.lifecycle_history_ids) <= found
        assert replica_group_history_seed.scaling_history_id in found
        assert replica_group_history_seed.other_group_history_id in found

    async def test_admin_search_with_category_filter_returns_only_matching_rows(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """A category filter on the unscoped admin route narrows to one handler family.

        Replica-group rows are written by two handler families, so ``category`` is the
        filter that separates them: scoping to SCALING must leave the seeded scaling row
        and drop every lifecycle row of the same group.
        """
        result = await admin_v2_registry.scheduling_history.search_replica_group_history(
            AdminSearchReplicaGroupHistoriesInput(
                filter=ReplicaGroupHistoryFilter(
                    category=[ReplicaGroupHistoryCategoryType.SCALING],
                ),
            )
        )

        found = {item.id for item in result.items}
        assert replica_group_history_seed.scaling_history_id in found
        assert not set(replica_group_history_seed.lifecycle_history_ids) & found

    async def test_admin_search_as_regular_user_is_rejected(
        self,
        user_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """The unscoped admin route is superadmin-only, so a regular user is refused.

        The route carries ``superadmin_required``; a non-superadmin caller must be rejected
        at the middleware rather than receive an empty page.
        """
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.scheduling_history.search_replica_group_history(
                AdminSearchReplicaGroupHistoriesInput()
            )


class TestScopedSearchReplicaGroupHistories:
    """``/replica-groups/scoped/search`` — the scope travels in the request body."""

    async def test_scoped_search_returns_every_replica_group_under_the_deployment(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """A deployment-scoped search returns the rows of every replica group it owns.

        The scope names the deployment, not one replica group, so the sibling group's row
        must be included alongside the first group's four; equality (not subset) pins that
        the scope covers exactly the deployment's rows.
        """
        result = await admin_v2_registry.scheduling_history.replica_group_scoped_search(
            ScopedSearchReplicaGroupHistoriesInput(
                scope=ReplicaGroupHistoryScopeDTO(
                    deployment=[UUIDScope(value=replica_group_history_seed.deployment_id)]
                ),
            )
        )

        assert isinstance(result, SearchReplicaGroupHistoriesPayload)
        assert {item.id for item in result.items} == {
            *replica_group_history_seed.lifecycle_history_ids,
            replica_group_history_seed.scaling_history_id,
            replica_group_history_seed.other_group_history_id,
        }

    async def test_scoped_search_with_unknown_deployment_returns_not_found(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """Scoping to a non-existent deployment fails the existence check and surfaces as a 404.

        The scoped route resolves the deployment before querying history, so a random
        deployment id must raise ``NotFoundError`` rather than return an empty page.
        """
        with pytest.raises(NotFoundError):
            await admin_v2_registry.scheduling_history.replica_group_scoped_search(
                ScopedSearchReplicaGroupHistoriesInput(
                    scope=ReplicaGroupHistoryScopeDTO(
                        deployment=[UUIDScope(value=DeploymentID(uuid.uuid4()))]
                    ),
                )
            )

    async def test_scoped_search_orders_by_attempts_ascending(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """An ``attempts`` ascending order round-trips through the HTTP boundary.

        The deployment's five rows carry ``attempts`` 1, 1, 1, 2, 3; requesting ASC order
        must return that sequence. The value list is stable even though the three
        attempt-1 rows tie.
        """
        result = await admin_v2_registry.scheduling_history.replica_group_scoped_search(
            ScopedSearchReplicaGroupHistoriesInput(
                scope=ReplicaGroupHistoryScopeDTO(
                    deployment=[UUIDScope(value=replica_group_history_seed.deployment_id)]
                ),
                order=[
                    ReplicaGroupHistoryOrder(
                        field=ReplicaGroupHistoryOrderField.ATTEMPTS,
                        direction=OrderDirection.ASC,
                    )
                ],
            )
        )

        assert [item.attempts for item in result.items] == [1, 1, 1, 2, 3]

    async def test_scoped_search_applies_limit_offset_pagination(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """``limit``/``offset`` shift the page while ``total_count`` stays the full size.

        With five rows ordered by ``attempts`` (1, 1, 1, 2, 3), ``limit=2, offset=3`` skips
        the three attempt-1 rows and returns the last two; the offset is large enough that
        the test fails if the field is dropped. ``total_count`` still reports all five.
        """
        result = await admin_v2_registry.scheduling_history.replica_group_scoped_search(
            ScopedSearchReplicaGroupHistoriesInput(
                scope=ReplicaGroupHistoryScopeDTO(
                    deployment=[UUIDScope(value=replica_group_history_seed.deployment_id)]
                ),
                order=[
                    ReplicaGroupHistoryOrder(
                        field=ReplicaGroupHistoryOrderField.ATTEMPTS,
                        direction=OrderDirection.ASC,
                    )
                ],
                limit=2,
                offset=3,
            )
        )

        assert [item.attempts for item in result.items] == [2, 3]
        assert result.total_count == 5

    async def test_scoped_search_applies_cursor_pagination(
        self,
        admin_v2_registry: V2ClientRegistry,
        replica_group_history_seed: ReplicaGroupHistorySeed,
    ) -> None:
        """``first`` cursor pagination returns a first page and reports a next page exists.

        With five rows under the deployment, ``first=2`` returns two items and
        ``has_next_page`` is True.
        """
        result = await admin_v2_registry.scheduling_history.replica_group_scoped_search(
            ScopedSearchReplicaGroupHistoriesInput(
                scope=ReplicaGroupHistoryScopeDTO(
                    deployment=[UUIDScope(value=replica_group_history_seed.deployment_id)]
                ),
                first=2,
            )
        )

        assert len(result.items) == 2
        assert result.has_next_page is True
