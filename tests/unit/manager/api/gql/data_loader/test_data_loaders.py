from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.kernel.response import (
    KernelLiveStatInfo,
    KernelLiveStatMetricInfo,
)
from ai.backend.common.dto.manager.v2.session_group.response import SessionGroupNode
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.kernel.types import KernelV2LiveStatGQL, KernelV2LiveStatMetricGQL
from ai.backend.manager.errors.permission import NotEnoughPermission


class TestSessionGroupLoader:
    @pytest.fixture
    def readable_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def empty_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def denied_id(self) -> SessionGroupID:
        return SessionGroupID(uuid.uuid4())

    @pytest.fixture
    def adapters(
        self, readable_id: SessionGroupID, empty_id: SessionGroupID, denied_id: SessionGroupID
    ) -> MagicMock:
        answers: dict[SessionGroupID, SessionGroupNode | Exception | None] = {
            readable_id: SessionGroupNode(
                id=readable_id,
                entity_id=readable_id,
                domain_id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                owner_user_id=uuid.uuid4(),
                placement_direction=SessionGroupPlacementDirectionEnum.PACK,
                placement_enforcement=SessionGroupPlacementEnforcementEnum.STRICT,
                created_at=datetime(2026, 10, 15, tzinfo=UTC),
            ),
            empty_id: None,
            denied_id: NotEnoughPermission(),
        }
        adapters = MagicMock()
        adapters.session_group.bulk_get_ids = AsyncMock(
            side_effect=lambda ids: [answers[group_id] for group_id in ids]
        )
        return adapters

    async def test_loads_for_many_sessions_read_the_groups_in_one_call(
        self,
        adapters: MagicMock,
        readable_id: SessionGroupID,
        empty_id: SessionGroupID,
    ) -> None:
        loader = DataLoaders(adapters).session_group_loader

        await asyncio.gather(loader.load(readable_id), loader.load(empty_id))

        adapters.session_group.bulk_get_ids.assert_awaited_once()

    async def test_each_id_gets_its_own_answer(
        self,
        adapters: MagicMock,
        readable_id: SessionGroupID,
        empty_id: SessionGroupID,
        denied_id: SessionGroupID,
    ) -> None:
        loader = DataLoaders(adapters).session_group_loader

        readable, empty, denied = await asyncio.gather(
            loader.load(readable_id),
            loader.load(empty_id),
            loader.load(denied_id),
            return_exceptions=True,
        )

        assert readable is not None
        assert not isinstance(readable, BaseException)
        assert readable.entity_id == readable_id
        assert empty is None
        assert isinstance(denied, NotEnoughPermission)


class TestKernelLiveStatLoader:
    @pytest.fixture
    def sampled_id(self) -> KernelID:
        return KernelID(uuid.uuid4())

    @pytest.fixture
    def unsampled_id(self) -> KernelID:
        return KernelID(uuid.uuid4())

    @pytest.fixture
    def adapters(self, sampled_id: KernelID, unsampled_id: KernelID) -> MagicMock:
        live_stat = KernelLiveStatInfo(
            metrics=[
                KernelLiveStatMetricInfo(
                    metric_name="cpu_util",
                    current="12.5",
                    capacity="400",
                    pct="3.12",
                    unit_hint="percent",
                    stats_max="20",
                    stats_avg="10",
                    stats_rate="0",
                    stats_diff="12.5",
                )
            ]
        )
        answers = {sampled_id: live_stat, unsampled_id: None}
        adapters = MagicMock()
        adapters.metric.batch_get_kernel_live_stats = AsyncMock(
            side_effect=lambda ids: [answers[kernel_id] for kernel_id in ids]
        )
        return adapters

    async def test_loads_for_many_kernels_read_the_stats_in_one_call(
        self, adapters: MagicMock, sampled_id: KernelID, unsampled_id: KernelID
    ) -> None:
        loader = DataLoaders(adapters).kernel_live_stat_loader

        sampled, unsampled = await asyncio.gather(
            loader.load(sampled_id), loader.load(unsampled_id)
        )

        adapters.metric.batch_get_kernel_live_stats.assert_awaited_once()
        assert isinstance(sampled, KernelV2LiveStatGQL)
        (metric,) = sampled.metrics
        assert isinstance(metric, KernelV2LiveStatMetricGQL)
        assert metric.metric_name == "cpu_util"
        assert metric.stats_diff == "12.5"
        assert unsampled is None
