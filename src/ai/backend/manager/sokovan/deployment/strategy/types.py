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
    DeploymentSubStep,
    RouteInfo,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator


@dataclass
class RouteChanges:
    """Route mutations to apply for a single deployment cycle."""

    rollout_specs: list[Creator[RoutingRow]] = field(default_factory=list)
    drain_route_ids: list[UUID] = field(default_factory=list)


@dataclass
class StrategyCycleResult:
    """Result of evaluating a single deployment's strategy cycle.

    ``sub_step`` indicates the next state: PROVISIONING, PROGRESSING,
    ROLLING_BACK, COMPLETED, or ROLLED_BACK.
    """

    sub_step: DeploymentSubStep
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
    the mapping so the evaluate handler can bulk-update the DB column.
    All outcomes — including ROLLING_BACK, COMPLETED, and ROLLED_BACK — are expressed
    as sub_step values and persisted to the DB for their respective handlers.
    """

    # Mapping from endpoint ID to its evaluated sub_step — used to bulk-update the DB.
    assignments: dict[UUID, DeploymentSubStep] = field(default_factory=dict)

    # Aggregated route mutations from all per-deployment evaluations.
    route_changes: RouteChanges = field(default_factory=RouteChanges)

    # Deployments that failed evaluation (no policy, strategy error, etc.)
    errors: list[EvaluationErrorData] = field(default_factory=list)


class AbstractDeploymentStrategy(ABC):
    """Base interface for deployment strategy cycle evaluation.

    Each concrete strategy (Blue-Green, Rolling Update) implements this interface.
    The spec is injected via ``__init__`` — one instance per deployment.
    """

    def __init__(self, spec: BaseModel) -> None:
        self._spec = spec

    @abstractmethod
    def evaluate_cycle(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
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
