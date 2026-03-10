"""Tests for StrategyResultApplier."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.manager.data.deployment.types import DeploymentSubStep
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.sokovan.deployment.strategy.applier import (
    StrategyApplyResult,
    StrategyResultApplier,
)
from ai.backend.manager.sokovan.deployment.strategy.types import (
    RouteChanges,
    StrategyEvaluationSummary,
)

# =============================================================================
# Helpers
# =============================================================================


def _build_summary(
    assignments: dict[UUID, DeploymentSubStep] | None = None,
    route_changes: RouteChanges | None = None,
) -> StrategyEvaluationSummary:
    return StrategyEvaluationSummary(
        assignments=assignments or {},
        route_changes=route_changes or RouteChanges(),
    )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_txn() -> AsyncMock:
    txn = AsyncMock()
    txn.apply_strategy_evaluation = AsyncMock()
    txn.complete_deployment_revision_swap = AsyncMock(return_value=0)
    txn.clear_deploying_revision = AsyncMock()
    return txn


@pytest.fixture
def mock_deployment_repo(mock_txn: AsyncMock) -> AsyncMock:
    repo = AsyncMock()
    repo.apply_strategy_evaluation = AsyncMock()

    @asynccontextmanager
    async def _begin_strategy_transaction() -> AsyncIterator[AsyncMock]:
        yield mock_txn

    repo.begin_strategy_transaction = _begin_strategy_transaction
    return repo


@pytest.fixture
def applier(mock_deployment_repo: AsyncMock) -> StrategyResultApplier:
    return StrategyResultApplier(deployment_repo=mock_deployment_repo)


@pytest.fixture
def empty_summary() -> StrategyEvaluationSummary:
    return _build_summary()


@pytest.fixture
def provisioning_summary() -> StrategyEvaluationSummary:
    return _build_summary({uuid4(): DeploymentSubStep.PROVISIONING})


@pytest.fixture
def summary_with_rollout() -> StrategyEvaluationSummary:
    return _build_summary(
        {uuid4(): DeploymentSubStep.PROVISIONING},
        route_changes=RouteChanges(rollout_specs=[MagicMock()]),
    )


@pytest.fixture
def summary_with_drain() -> StrategyEvaluationSummary:
    return _build_summary(
        {uuid4(): DeploymentSubStep.PROGRESSING},
        route_changes=RouteChanges(drain_route_ids=[uuid4()]),
    )


@pytest.fixture
def completed_summary() -> tuple[StrategyEvaluationSummary, set[UUID]]:
    ep_id_1 = uuid4()
    ep_id_2 = uuid4()
    completed_ids = {ep_id_1, ep_id_2}
    summary = _build_summary({
        ep_id_1: DeploymentSubStep.COMPLETED,
        ep_id_2: DeploymentSubStep.COMPLETED,
    })
    return summary, completed_ids


@pytest.fixture
def rolled_back_summary() -> tuple[StrategyEvaluationSummary, set[UUID]]:
    ep_id = uuid4()
    summary = _build_summary({ep_id: DeploymentSubStep.ROLLED_BACK})
    return summary, {ep_id}


@pytest.fixture
def mixed_summary() -> tuple[StrategyEvaluationSummary, UUID, UUID, UUID]:
    provisioning_id = uuid4()
    completed_id = uuid4()
    rolled_back_id = uuid4()
    summary = _build_summary(
        {
            provisioning_id: DeploymentSubStep.PROVISIONING,
            completed_id: DeploymentSubStep.COMPLETED,
            rolled_back_id: DeploymentSubStep.ROLLED_BACK,
        },
        route_changes=RouteChanges(
            rollout_specs=[MagicMock()],
            drain_route_ids=[uuid4()],
        ),
    )
    return summary, provisioning_id, completed_id, rolled_back_id


# =============================================================================
# Tests
# =============================================================================


class TestStrategyResultApplier:
    """Tests for StrategyResultApplier.apply()."""

    async def test_empty_summary_skips_all_db_calls(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        empty_summary: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(empty_summary)

        mock_txn.apply_strategy_evaluation.assert_not_called()
        mock_txn.complete_deployment_revision_swap.assert_not_called()
        mock_txn.clear_deploying_revision.assert_not_called()
        assert result.completed_ids == set()
        assert result.rolled_back_ids == set()
        assert result.routes_created == 0
        assert result.routes_drained == 0

    async def test_assignments_only_calls_apply_strategy_evaluation(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        provisioning_summary: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(provisioning_summary)

        mock_txn.apply_strategy_evaluation.assert_called_once()
        mock_txn.complete_deployment_revision_swap.assert_not_called()
        mock_txn.clear_deploying_revision.assert_not_called()
        assert result.routes_created == 0
        assert result.routes_drained == 0

    async def test_rollout_specs_creates_bulk_creator(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        summary_with_rollout: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(summary_with_rollout)

        mock_txn.apply_strategy_evaluation.assert_called_once()
        args = mock_txn.apply_strategy_evaluation.call_args
        rollout_arg: BulkCreator[RoutingRow] = args[0][1]
        assert len(rollout_arg.specs) == 1
        assert result.routes_created == 1

    async def test_drain_route_ids_creates_batch_updater(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        summary_with_drain: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(summary_with_drain)

        mock_txn.apply_strategy_evaluation.assert_called_once()
        args = mock_txn.apply_strategy_evaluation.call_args
        drain_arg: BatchUpdater[RoutingRow] | None = args[0][2]
        assert drain_arg is not None
        assert result.routes_drained == 1

    async def test_no_drain_routes_passes_none(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        provisioning_summary: StrategyEvaluationSummary,
    ) -> None:
        await applier.apply(provisioning_summary)

        args = mock_txn.apply_strategy_evaluation.call_args
        drain_arg = args[0][2]
        assert drain_arg is None

    async def test_completed_calls_revision_swap(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        completed_summary: tuple[StrategyEvaluationSummary, set[UUID]],
    ) -> None:
        summary, completed_ids = completed_summary
        mock_txn.complete_deployment_revision_swap.return_value = 2

        result = await applier.apply(summary)

        mock_txn.apply_strategy_evaluation.assert_called_once()
        mock_txn.complete_deployment_revision_swap.assert_called_once_with(completed_ids)
        mock_txn.clear_deploying_revision.assert_not_called()
        assert result.completed_ids == completed_ids

    async def test_rolled_back_calls_clear_deploying_revision(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        rolled_back_summary: tuple[StrategyEvaluationSummary, set[UUID]],
    ) -> None:
        summary, rolled_back_ids = rolled_back_summary

        result = await applier.apply(summary)

        mock_txn.apply_strategy_evaluation.assert_called_once()
        mock_txn.clear_deploying_revision.assert_called_once_with(rolled_back_ids)
        mock_txn.complete_deployment_revision_swap.assert_not_called()
        assert result.rolled_back_ids == rolled_back_ids

    async def test_mixed_assignments_handles_all(
        self,
        applier: StrategyResultApplier,
        mock_txn: AsyncMock,
        mixed_summary: tuple[StrategyEvaluationSummary, UUID, UUID, UUID],
    ) -> None:
        summary, _provisioning_id, completed_id, rolled_back_id = mixed_summary
        mock_txn.complete_deployment_revision_swap.return_value = 1

        result = await applier.apply(summary)

        mock_txn.apply_strategy_evaluation.assert_called_once()
        mock_txn.complete_deployment_revision_swap.assert_called_once_with({completed_id})
        mock_txn.clear_deploying_revision.assert_called_once_with({rolled_back_id})
        assert result.completed_ids == {completed_id}
        assert result.rolled_back_ids == {rolled_back_id}
        assert result.routes_created == 1
        assert result.routes_drained == 1

    async def test_result_type_is_strategy_apply_result(
        self,
        applier: StrategyResultApplier,
        empty_summary: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(empty_summary)

        assert isinstance(result, StrategyApplyResult)
