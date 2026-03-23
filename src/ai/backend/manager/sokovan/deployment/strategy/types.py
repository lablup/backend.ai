"""Types for deployment strategy evaluation (BEP-1049)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from pydantic import BaseModel

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    RouteInfo,
)
from ai.backend.manager.models.deployment_policy import DeploymentStrategySpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator


@dataclass
class RouteChanges:
    """Route mutations to apply for a single deployment cycle."""

    rollout_specs: list[RBACEntityCreator[RoutingRow]] = field(default_factory=list)
    drain_route_ids: list[UUID] = field(default_factory=list)


@dataclass
class StrategyCycleResult:
    """Result of evaluating a single deployment's strategy cycle.

    ``sub_step`` indicates the next state: PROVISIONING or COMPLETED.
    """

    sub_step: DeploymentLifecycleSubStep
    route_changes: RouteChanges = field(default_factory=RouteChanges)


@dataclass
class EvaluationErrorData:
    """Data about a deployment that failed strategy evaluation."""

    deployment: DeploymentInfo
    reason: str


@dataclass
class StrategyEvaluationSummary:
    """Aggregate result of evaluating all DEPLOYING deployments.

    The evaluator classifies each deployment into a sub_step and records
    the mapping.  The applier uses COMPLETED assignments to trigger
    revision swaps.  Sub-step transitions are handled by the coordinator.
    """

    # Mapping from endpoint ID to its evaluated sub_step — used to bulk-update the DB.
    assignments: dict[UUID, DeploymentLifecycleSubStep] = field(default_factory=dict)

    # Aggregated route mutations from all per-deployment evaluations.
    route_changes: RouteChanges = field(default_factory=RouteChanges)

    # Deployments that failed evaluation or have failed routes.
    errors: list[EvaluationErrorData] = field(default_factory=list)


class AbstractDeploymentStrategy(ABC):
    """Base interface for deployment strategy cycle evaluation.

    Each concrete strategy (Blue-Green, Rolling Update) implements this interface.
    The spec is passed per-cycle via ``evaluate_cycle``.
    """

    @abstractmethod
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
        spec: DeploymentStrategySpec,
    ) -> StrategyCycleResult: ...


@dataclass(frozen=True)
class DeploymentStrategyRegistryEntry:
    """Maps a deployment strategy to its implementation class and expected spec type."""

    strategy_cls: type[AbstractDeploymentStrategy]
    spec_type: type[BaseModel]


class DeploymentStrategyRegistry:
    """Registry of deployment strategy implementations."""

    def __init__(self) -> None:
        self._entries: dict[DeploymentStrategy, DeploymentStrategyRegistryEntry] = {}

    def register(
        self,
        strategy: DeploymentStrategy,
        strategy_cls: type[AbstractDeploymentStrategy],
        spec_type: type[BaseModel],
    ) -> None:
        self._entries[strategy] = DeploymentStrategyRegistryEntry(strategy_cls, spec_type)

    def get(self, strategy: DeploymentStrategy) -> DeploymentStrategyRegistryEntry | None:
        return self._entries.get(strategy)
