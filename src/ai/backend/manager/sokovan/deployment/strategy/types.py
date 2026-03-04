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
class CycleEvaluationResult:
    """Result of evaluating a single deployment's strategy cycle."""

    sub_step: DeploymentSubStep
    completed: bool = False
    route_changes: RouteChanges = field(default_factory=RouteChanges)


@dataclass
class EvaluationGroup:
    """Deployments grouped by their sub-step result."""

    sub_step: DeploymentSubStep
    deployments: list[DeploymentInfo] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Aggregate result of evaluating all DEPLOYING deployments."""

    # In-progress deployments grouped by sub-step (PROVISIONING, PROGRESSING, etc.).
    # The coordinator looks up the handler for each sub-step and calls execute().
    groups: dict[DeploymentSubStep, EvaluationGroup] = field(default_factory=dict)

    # Deployments that satisfied all strategy FSM conditions and are ready to finish.
    # The coordinator performs an atomic revision swap + READY transition for these.
    completed: list[DeploymentInfo] = field(default_factory=list)

    # Maps each completed deployment to the strategy (ROLLING, BLUE_GREEN) it used.
    # The coordinator includes this in the history message for observability.
    completed_strategies: dict[UUID, DeploymentStrategy] = field(default_factory=dict)

    # Deployments skipped because no deployment policy was found.
    # The coordinator records SKIPPED history and emits a warning log.
    skipped: list[DeploymentInfo] = field(default_factory=list)

    # Deployments that raised an exception during strategy FSM evaluation, paired
    # with the error message. The coordinator records NEED_RETRY history and keeps
    # the lifecycle at DEPLOYING so the next cycle can retry.
    errors: list[tuple[DeploymentInfo, str]] = field(default_factory=list)

    # Aggregated route mutations from all per-deployment evaluations.
    # The coordinator applies these after evaluation completes.
    route_changes: RouteChanges = field(default_factory=RouteChanges)


class BaseDeploymentStrategy(ABC):
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
    ) -> CycleEvaluationResult: ...
