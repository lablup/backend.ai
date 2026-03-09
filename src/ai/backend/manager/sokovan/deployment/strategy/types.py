"""Types for deployment strategy evaluation (BEP-1049)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from pydantic import BaseModel

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
    """Result of evaluating a single deployment's strategy cycle.

    ``sub_step`` indicates the next state: PROVISIONING, PROGRESSING,
    COMPLETED, or ROLLED_BACK.
    """

    sub_step: DeploymentSubStep
    route_changes: RouteChanges = field(default_factory=RouteChanges)


@dataclass
class EvaluationResult:
    """Aggregate result of evaluating all DEPLOYING deployments.

    The evaluator classifies each deployment into a sub_step and records
    the mapping so the evaluate handler can bulk-update the DB column.
    All outcomes — including COMPLETED and ROLLED_BACK — are expressed
    as sub_step values and persisted to the DB for their respective handlers.
    """

    # Mapping from sub_step to endpoint IDs — used to bulk-update the DB.
    assignments: defaultdict[DeploymentSubStep, set[UUID]] = field(
        default_factory=lambda: defaultdict(set)
    )

    # Aggregated route mutations from all per-deployment evaluations.
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
