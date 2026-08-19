"""Tests for the Fair Share sequencer."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from decimal import Decimal
from unittest.mock import AsyncMock

from ai.backend.common.identifier.user import UserID
from ai.backend.manager.data.fair_share import ProjectUserIds, UserFairShareFactors
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fair_share import (
    FairShareSequencer,
)
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .conftest import RESOURCE_GROUP_ID

WorkloadFactory = Callable[..., SessionWorkload]


def _factors(
    workload: SessionWorkload,
    domain_factor: str,
    project_factor: str = "0",
    user_factor: str = "0",
) -> UserFairShareFactors:
    return UserFairShareFactors(
        user_uuid=workload.meta.owner.user_uuid,
        project_id=workload.meta.owner.project_id,
        domain_name="default",
        domain_factor=Decimal(domain_factor),
        project_factor=Decimal(project_factor),
        user_factor=Decimal(user_factor),
    )


class TestFairShareSequencer:
    def test_name(self) -> None:
        assert FairShareSequencer(AsyncMock()).name == "FairShareSequencer"

    async def test_empty_workload_skips_repository(
        self,
        empty_snapshot: SystemSnapshot,
    ) -> None:
        repository = AsyncMock()
        sequencer = FairShareSequencer(repository)

        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [])

        assert list(result) == []
        repository.get_user_fair_share_factors_batch.assert_not_called()

    async def test_loads_factors_by_resource_group_id(
        self,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        """Factors are fetched once for the resource group with grouped users."""
        workload = workload_factory(user_id=UserID(uuid.uuid4()))
        repository = AsyncMock()
        repository.get_user_fair_share_factors_batch.return_value = {}
        sequencer = FairShareSequencer(repository)

        await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [workload])

        repository.get_user_fair_share_factors_batch.assert_awaited_once()
        called_rg_id, called_project_users = (
            repository.get_user_fair_share_factors_batch.await_args_list[0].args
        )
        assert called_rg_id == RESOURCE_GROUP_ID
        assert called_project_users == [
            ProjectUserIds(
                project_id=workload.meta.owner.project_id,
                user_ids=frozenset({workload.meta.owner.user_uuid}),
            )
        ]

    async def test_orders_by_factors_descending(
        self,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        """Higher factors (lower historical usage) are scheduled first."""
        low = workload_factory(user_id=UserID(uuid.uuid4()))
        high = workload_factory(user_id=UserID(uuid.uuid4()))
        repository = AsyncMock()
        repository.get_user_fair_share_factors_batch.return_value = {
            low.meta.owner.user_uuid: _factors(low, domain_factor="0.1"),
            high.meta.owner.user_uuid: _factors(high, domain_factor="0.9"),
        }
        sequencer = FairShareSequencer(repository)

        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [low, high])

        assert list(result) == [high, low]

    async def test_missing_factors_get_lowest_priority(
        self,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        """A user without recorded factors is placed last."""
        known = workload_factory(user_id=UserID(uuid.uuid4()))
        unknown = workload_factory(user_id=UserID(uuid.uuid4()))
        repository = AsyncMock()
        repository.get_user_fair_share_factors_batch.return_value = {
            known.meta.owner.user_uuid: _factors(known, domain_factor="0.5"),
        }
        sequencer = FairShareSequencer(repository)

        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [unknown, known])

        assert list(result) == [known, unknown]
