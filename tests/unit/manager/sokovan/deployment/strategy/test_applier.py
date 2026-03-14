"""Tests for StrategyResultApplier."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.manager.data.deployment.types import DeploymentSubStep
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
def mock_deployment_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.apply_strategy_mutations = AsyncMock(return_value=0)
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
        mock_deployment_repo: AsyncMock,
        empty_summary: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(empty_summary)

        mock_deployment_repo.apply_strategy_mutations.assert_not_called()
        assert result.completed_ids == set()
        assert result.rolled_back_ids == set()
        assert result.routes_created == 0
        assert result.routes_drained == 0

    async def test_assignments_only(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        provisioning_summary: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(provisioning_summary)

        mock_deployment_repo.apply_strategy_mutations.assert_called_once()
        kwargs = mock_deployment_repo.apply_strategy_mutations.call_args.kwargs
        assert kwargs["completed_ids"] == set()
        assert kwargs["rolled_back_ids"] == set()
        assert kwargs["drain"] is None
        assert not kwargs["rollout"]
        assert result.routes_created == 0
        assert result.routes_drained == 0

    async def test_rollout_passes_specs(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        summary_with_rollout: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(summary_with_rollout)

        mock_deployment_repo.apply_strategy_mutations.assert_called_once()
        kwargs = mock_deployment_repo.apply_strategy_mutations.call_args.kwargs
        assert len(kwargs["rollout"]) == 1
        assert result.routes_created == 1

    async def test_drain_passes_updater(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        summary_with_drain: StrategyEvaluationSummary,
    ) -> None:
        result = await applier.apply(summary_with_drain)

        mock_deployment_repo.apply_strategy_mutations.assert_called_once()
        kwargs = mock_deployment_repo.apply_strategy_mutations.call_args.kwargs
        assert kwargs["drain"] is not None
        assert result.routes_drained == 1

    async def test_no_drain_routes_passes_none(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        provisioning_summary: StrategyEvaluationSummary,
    ) -> None:
        await applier.apply(provisioning_summary)

        kwargs = mock_deployment_repo.apply_strategy_mutations.call_args.kwargs
        assert kwargs["drain"] is None

    async def test_completed_passes_completed_ids(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        completed_summary: tuple[StrategyEvaluationSummary, set[UUID]],
    ) -> None:
        summary, completed_ids = completed_summary
        mock_deployment_repo.apply_strategy_mutations.return_value = 2

        result = await applier.apply(summary)

        kwargs = mock_deployment_repo.apply_strategy_mutations.call_args.kwargs
        assert kwargs["completed_ids"] == completed_ids
        assert kwargs["rolled_back_ids"] == set()
        assert result.completed_ids == completed_ids

    async def test_rolled_back_passes_rolled_back_ids(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        rolled_back_summary: tuple[StrategyEvaluationSummary, set[UUID]],
    ) -> None:
        summary, rolled_back_ids = rolled_back_summary

        result = await applier.apply(summary)

        kwargs = mock_deployment_repo.apply_strategy_mutations.call_args.kwargs
        assert kwargs["rolled_back_ids"] == rolled_back_ids
        assert kwargs["completed_ids"] == set()
        assert result.rolled_back_ids == rolled_back_ids

    async def test_mixed_assignments_handles_all(
        self,
        applier: StrategyResultApplier,
        mock_deployment_repo: AsyncMock,
        mixed_summary: tuple[StrategyEvaluationSummary, UUID, UUID, UUID],
    ) -> None:
        summary, _provisioning_id, completed_id, rolled_back_id = mixed_summary
        mock_deployment_repo.apply_strategy_mutations.return_value = 1

        result = await applier.apply(summary)

        mock_deployment_repo.apply_strategy_mutations.assert_called_once()
        kwargs = mock_deployment_repo.apply_strategy_mutations.call_args.kwargs
        assert kwargs["completed_ids"] == {completed_id}
        assert kwargs["rolled_back_ids"] == {rolled_back_id}
        assert len(kwargs["rollout"]) == 1
        assert kwargs["drain"] is not None
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
