"""Types for deployment strategy evaluation (BEP-1049)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentSubStep,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator


@dataclass
class RouteChanges:
    """Route mutations to apply for a single deployment cycle."""

    scale_out_specs: list[Creator[RoutingRow]] = field(default_factory=list)
    scale_in_route_ids: list[UUID] = field(default_factory=list)
    promote_route_ids: list[UUID] = field(default_factory=list)


@dataclass
class CycleEvaluationResult:
    """Result of evaluating a single deployment's rolling update cycle."""

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

    groups: dict[DeploymentSubStep, EvaluationGroup] = field(default_factory=dict)
    completed: list[DeploymentInfo] = field(default_factory=list)
    skipped: list[DeploymentInfo] = field(default_factory=list)
    errors: list[tuple[DeploymentInfo, str]] = field(default_factory=list)
