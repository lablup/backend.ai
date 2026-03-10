"""Tests for StrategyResultApplier."""

from __future__ import annotations

from collections import defaultdict
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
    assignments: dict[DeploymentSubStep, set[UUID]] | None = None,
    route_changes: RouteChanges | None = None,
) -> StrategyEvaluationSummary:
    assignment_map: defaultdict[DeploymentSubStep, set[UUID]] = defaultdict(set)
    if assignments:
        for sub_step, endpoint_ids in assignments.items():
            assignment_map[sub_step] = endpoint_ids
    return StrategyEvaluationSummary(
        assignments=assignment_map,
        route_changes=route_changes or RouteChanges(),
    )


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_deployment_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.apply_strategy_evaluation = AsyncMock(return_value=None)
    repo.complete_deployment_revision_swap = AsyncMock(return_value=0)
    repo.clear_deploying_revision = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def applier(mock_deployment_repo: AsyncMock) -> StrategyResultApplier:
    return StrategyResultApplier(deployment_repo=mock_deployment_repo)


@pytest.fixture
def empty_summary() -> StrategyEvaluationSummary:
    return _build_summary()


@pytest.fixture
def provisioning_summary() -> StrategyEvaluationSummary:
    return _build_summary({DeploymentSubStep.PROVISIONING: {uuid4()}})


@pytest.fixture
def summary_with_rollout() -> StrategyEvaluationSummary:
    return _build_summary(
        {DeploymentSubStep.PROVISIONING: {uuid4()}},
        route_changes=RouteChanges(rollout_specs=[MagicMock()]),
    )


@pytest.fixture
def summary_with_drain() -> StrategyEvaluationSummary:
    return _build_summary(
        {DeploymentSubStep.PROGRESSING: {uuid4()}},
        route_changes=RouteChanges(drain_route_ids=[uuid4()]),
    )


@pytest.fixture
def completed_summary() -> tuple[StrategyEvaluationSummary, set[UUID]]:
    ids = {uuid4(), uuid4()}
    return _build_summary({DeploymentSubStep.COMPLETED: ids}), ids


@pytest.fixture
def rolled_back_summary() -> tuple[StrategyEvaluationSummary, set[UUID]]:
    ids = {uuid4()}
    return _build_summary({DeploymentSubStep.ROLLED_BACK: ids}), ids


@pytest.fixture
def mixed_summary() -> tuple[StrategyEvaluationSummary, UUID, UUID, UUID]:
    provisioning_id = uuid4()
    completed_id = uuid4()
    rolled_back_id = uuid4()
    summary = _build_summary(
        {
            DeploymentSubStep.PROVISIONING: {provisioning_id},
            DeploymentSubStep.COMPLETED: {completed_id},
            DeploymentSubStep.ROLLED_BACK: {rolled_back_id},
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
        mock_deployment_repo: AsyncMock,
        empty_summary: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(empty_summary)

        mock_deployment_repo.apply_strategy_evaluation.assert_not_called()
        mock_deployment_repo.complete_deployment_revision_swap.assert_not_called()
        mock_deployment_repo.clear_deploying_revision.assert_not_called()
        assert result.completed_ids == set()
        assert result.rolled_back_ids == set()
        assert result.routes_created == 0
        assert result.routes_drained == 0

    async def test_assignments_only_calls_apply_strategy_evaluation(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        provisioning_summary: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(provisioning_summary)

        mock_deployment_repo.apply_strategy_evaluation.assert_called_once()
        mock_deployment_repo.complete_deployment_revision_swap.assert_not_called()
        mock_deployment_repo.clear_deploying_revision.assert_not_called()
        assert result.routes_created == 0
        assert result.routes_drained == 0

    async def test_rollout_specs_creates_bulk_creator(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        summary_with_rollout: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(summary_with_rollout)

        mock_deployment_repo.apply_strategy_evaluation.assert_called_once()
        args = mock_deployment_repo.apply_strategy_evaluation.call_args
        rollout_arg: BulkCreator[RoutingRow] = args[0][1]
        assert len(rollout_arg.specs) == 1
        assert result.routes_created == 1

    async def test_drain_route_ids_creates_batch_updater(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        summary_with_drain: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(summary_with_drain)

        mock_deployment_repo.apply_strategy_evaluation.assert_called_once()
        args = mock_deployment_repo.apply_strategy_evaluation.call_args
        drain_arg: BatchUpdater[RoutingRow] | None = args[0][2]
        assert drain_arg is not None
        assert result.routes_drained == 1

    async def test_no_drain_routes_passes_none(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        provisioning_summary: StrategyEvaluationSummary,
    ) -> None:
        await applier.apply(provisioning_summary)

        args = mock_deployment_repo.apply_strategy_evaluation.call_args
        drain_arg = args[0][2]
        assert drain_arg is None

    async def test_completed_assignments_triggers_revision_swap(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        completed_summary: tuple[StrategyEvaluationSummary, set[UUID]],
    ) -> None:
        summary, completed_ids = completed_summary
        mock_deployment_repo.complete_deployment_revision_swap.return_value = 2

        result = await applier.apply(summary)

        mock_deployment_repo.complete_deployment_revision_swap.assert_called_once_with(
            completed_ids
        )
        assert result.completed_ids == completed_ids

    async def test_rolled_back_assignments_clears_deploying_revision(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        rolled_back_summary: tuple[StrategyEvaluationSummary, set[UUID]],
    ) -> None:
        summary, rolled_back_ids = rolled_back_summary

        result = await applier.apply(summary)

        mock_deployment_repo.clear_deploying_revision.assert_called_once_with(rolled_back_ids)
        assert result.rolled_back_ids == rolled_back_ids

    async def test_mixed_assignments_handles_all(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        mixed_summary: tuple[StrategyEvaluationSummary, UUID, UUID, UUID],
    ) -> None:
        summary, _provisioning_id, completed_id, rolled_back_id = mixed_summary
        mock_deployment_repo.complete_deployment_revision_swap.return_value = 1

        result = await applier.apply(summary)

        mock_deployment_repo.apply_strategy_evaluation.assert_called_once()
        mock_deployment_repo.complete_deployment_revision_swap.assert_called_once_with(
            {completed_id}
        )
        mock_deployment_repo.clear_deploying_revision.assert_called_once_with({rolled_back_id})
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
