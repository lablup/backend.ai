from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ai.backend.appproxy.common.errors import WorkerNotAvailable
from ai.backend.appproxy.worker.proxy.backend.pool import RoutePool, RoutePoolSpec
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    IngressBackend,
    IngressBackendID,
    IngressTarget,
    IngressTargetGroup,
    IngressTargetGroupID,
    IngressTargetID,
)

_GROUP_ID = IngressTargetGroupID("00000000-0000-0000-0000-000000000000")
_BACKEND_ID = IngressBackendID("00000000-0000-0000-0000-000000000000")
_TARGET_A = IngressTarget(
    id=IngressTargetID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), host="10.0.0.1", port=8000
)
_TARGET_B = IngressTarget(
    id=IngressTargetID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"), host="10.0.0.2", port=8000
)
_TARGET_A_MOVED = _TARGET_A.model_copy(update={"host": "10.0.0.9"})
_SPEC = RoutePoolSpec(failure_threshold=1, health_check_interval=3600.0)


class TestRoutePool:
    @pytest.fixture
    async def pool_with_a_weighted_and_an_unweighted_group(self) -> AsyncIterator[RoutePool]:
        pool = RoutePool(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[
                    IngressTargetGroup(id=_GROUP_ID, weight=0, targets=[_TARGET_A]),
                    IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_B]),
                ],
            ),
            spec=_SPEC,
        )
        yield pool
        await pool.close()

    @pytest.fixture
    async def pool_holding_target_a_marked_unhealthy(self) -> AsyncIterator[RoutePool]:
        pool = RoutePool(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_A])],
            ),
            spec=_SPEC,
        )
        pool.record_failure(_TARGET_A)
        yield pool
        await pool.close()

    async def test_select_skips_a_group_with_no_weight(
        self, pool_with_a_weighted_and_an_unweighted_group: RoutePool
    ) -> None:
        assert await pool_with_a_weighted_and_an_unweighted_group.select() == _TARGET_B

    async def test_update_keeps_the_health_of_a_target_at_the_same_address(
        self, pool_holding_target_a_marked_unhealthy: RoutePool
    ) -> None:
        pool = pool_holding_target_a_marked_unhealthy
        await pool.update(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_A])],
            )
        )
        with pytest.raises(WorkerNotAvailable):
            await pool.select()

    async def test_update_starts_a_target_moved_to_a_new_address_healthy(
        self, pool_holding_target_a_marked_unhealthy: RoutePool
    ) -> None:
        pool = pool_holding_target_a_marked_unhealthy
        await pool.update(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[
                    IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_A_MOVED])
                ],
            )
        )
        assert await pool.select() == _TARGET_A_MOVED

    async def test_update_drops_a_target_missing_from_the_backend(
        self, pool_holding_target_a_marked_unhealthy: RoutePool
    ) -> None:
        pool = pool_holding_target_a_marked_unhealthy
        await pool.update(
            IngressBackend(
                id=_BACKEND_ID,
                target_groups=[IngressTargetGroup(id=_GROUP_ID, weight=100, targets=[_TARGET_B])],
            )
        )
        assert await pool.select() == _TARGET_B
