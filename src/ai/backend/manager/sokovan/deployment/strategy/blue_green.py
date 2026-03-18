"""Blue-green deployment strategy evaluation for a single deployment cycle (BEP-1049).

Provisions a full set of new-revision routes, validates them, then atomically
switches traffic from the old revision to the new one.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    RouteInfo,
)
from ai.backend.manager.models.deployment_policy import BlueGreenSpec

from .types import AbstractDeploymentStrategy, StrategyCycleResult


class BlueGreenStrategy(AbstractDeploymentStrategy):
    """Blue-green deployment strategy FSM."""

    def __init__(self, spec: BlueGreenSpec) -> None:
        super().__init__(spec)
        self._spec = spec

    @override
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
    ) -> StrategyCycleResult:
        """Evaluate one cycle of blue-green deployment for a single deployment."""
        raise NotImplementedError("Blue-green deployment strategy is not yet implemented")
