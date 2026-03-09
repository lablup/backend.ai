"""Rolling update strategy evaluation for a single deployment cycle (BEP-1049).

Classifies routes by revision (old/new) and status, then decides the next
sub-step and route mutations based on ``max_surge`` / ``max_unavailable``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    RouteInfo,
)
from ai.backend.manager.models.deployment_policy import RollingUpdateSpec

from .types import AbstractDeploymentStrategy, CycleEvaluationResult


class RollingUpdateStrategy(AbstractDeploymentStrategy):
    """Rolling update deployment strategy FSM."""

    def __init__(self, spec: RollingUpdateSpec) -> None:
        super().__init__(spec)
        self._spec = spec

    @override
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
    ) -> CycleEvaluationResult:
        """Evaluate one cycle of rolling update for a single deployment."""
        raise NotImplementedError("Rolling update strategy is not yet implemented")
