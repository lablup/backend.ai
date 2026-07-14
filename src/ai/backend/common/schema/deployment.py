"""Deployment strategy schemas and the plain value types they operate on, shared between the
manager and its data layer. The specs are pydantic schema definitions usable as pydantic column
types (persisted as JSON on ORM rows); the value dataclasses carry the I/O of the strategy
methods with no side effects."""

from __future__ import annotations

import math
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import override

from pydantic import Field, model_validator

from ai.backend.common.types import BackendAISchema

__all__ = (
    "BlueGreenSpec",
    "CanarySpec",
    "DeploymentStrategySchema",
    "IntOrPercent",
    "ReplicaGroupRolloutSpec",
    "RollingUpdateSpec",
    "TargetGroupSpec",
    "TrafficStep",
    "TrafficStepInput",
)


class IntOrPercent(BackendAISchema):
    """A rolling-update budget value: either an absolute count or a percentage.

    Exactly one of ``count`` or ``percent`` must be provided (oneOf semantics).

    - ``{"count": 2}``        — absolute replica count
    - ``{"percent": 0.25}``   — fraction of desired replicas (0.0-1.0)
    """

    count: int | None = Field(default=None, ge=0)
    percent: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_one_of(self) -> IntOrPercent:
        has_count = self.count is not None
        has_percent = self.percent is not None
        if has_count == has_percent:
            raise ValueError("Exactly one of 'count' or 'percent' must be provided.")
        return self

    @property
    def is_count(self) -> bool:
        return self.count is not None

    @property
    def is_percent(self) -> bool:
        return self.percent is not None

    @property
    def is_zero(self) -> bool:
        if self.count is not None:
            return self.count == 0
        return self.percent == 0.0


class ReplicaGroupRolloutSpec(BackendAISchema):
    """Per-group rollout step config snapshot from the deployment strategy at
    DEPLOYING_INITIALIZING; bounds how fast routes move toward the group's desired counts."""

    max_surge: IntOrPercent
    max_unavailable: IntOrPercent

    def resolve_max_surge(self, total: int) -> int:
        """Extra target replicas allowed above the goal (rounds up for percentages)."""
        return self._resolve(self.max_surge, total, round_up=True)

    def resolve_max_unavailable(self, total: int) -> int:
        """Replicas allowed unavailable below the goal (rounds down for percentages)."""
        return self._resolve(self.max_unavailable, total, round_up=False)

    @staticmethod
    def _resolve(value: IntOrPercent, total: int, *, round_up: bool) -> int:
        if value.count is not None:
            return value.count
        result = total * (value.percent or 0.0)
        return math.ceil(result) if round_up else math.floor(result)


@dataclass(frozen=True)
class TargetGroupSpec:
    """How the deploying revision's target group is chosen. ``use_primary_group`` True rolls out
    in place into the deployment's primary group (rolling) — the setup reads that group at creation
    time and creates a fresh one if none exists yet. When False, a fresh group is always created
    (blue-green/canary).

    No traffic weight here: a freshly rolled-out group serves no traffic until PROMOTING shifts
    it over, so PROVISIONING creates it at weight 0 and leaves a reused group's weight untouched."""

    use_primary_group: bool
    rollout: ReplicaGroupRolloutSpec


@dataclass(frozen=True)
class TrafficStepInput:
    """Current traffic split + timing for one PROMOTING tick (step is relative to current)."""

    target_traffic_weight: int
    serving_traffic_weight: int
    last_changed_at: datetime
    now: datetime


@dataclass(frozen=True)
class TrafficStep:
    """The next traffic split (target/serving) and whether promotion is complete."""

    target_traffic_weight: int
    serving_traffic_weight: int
    completed: bool


class DeploymentStrategySchema(BackendAISchema):
    """Base for deployment strategy specs: each strategy decides the group its revision rolls
    out into and how traffic promotes to it. I/O are plain data dataclasses, no side effects."""

    @abstractmethod
    def rollout_target(self) -> TargetGroupSpec:
        """How the deploying revision's target group is chosen (reuse primary / create new)."""
        raise NotImplementedError

    @abstractmethod
    def traffic_step(self, step_input: TrafficStepInput) -> TrafficStep:
        """The next traffic split toward the target group and whether promotion is complete."""
        raise NotImplementedError


class RollingUpdateSpec(DeploymentStrategySchema):
    """Specification for rolling update deployment strategy.

    ``max_surge`` and ``max_unavailable`` are :class:`IntOrPercent` objects.
    Percentage values are resolved to absolute counts at execution time via
    :meth:`resolve_max_surge` / :meth:`resolve_max_unavailable`.
    """

    max_surge: IntOrPercent = Field(default_factory=lambda: IntOrPercent(percent=0.5))
    max_unavailable: IntOrPercent = Field(default_factory=lambda: IntOrPercent(percent=0.0))

    @override
    def rollout_target(self) -> TargetGroupSpec:
        return TargetGroupSpec(use_primary_group=True, rollout=self.to_rollout_spec())

    @override
    def traffic_step(self, step_input: TrafficStepInput) -> TrafficStep:
        return TrafficStep(target_traffic_weight=100, serving_traffic_weight=0, completed=True)

    @model_validator(mode="after")
    def _validate_progress_is_possible(self) -> RollingUpdateSpec:
        """Ensure at least one of max_surge or max_unavailable is positive.

        If both are zero the rolling update FSM cannot make progress:
        it cannot create new routes (would exceed max_total) nor terminate
        old routes (would fall below min_available), causing a deadlock.
        """
        if self.max_surge.is_zero and self.max_unavailable.is_zero:
            raise ValueError(
                "At least one of max_surge or max_unavailable must be positive; "
                "otherwise the rolling update cannot make progress."
            )
        return self

    def to_rollout_spec(self) -> ReplicaGroupRolloutSpec:
        """The per-group rollout step: rolling updates surge/drain in place."""
        return ReplicaGroupRolloutSpec(
            max_surge=self.max_surge,
            max_unavailable=self.max_unavailable,
        )

    def resolve_max_surge(self, desired_replicas: int) -> int:
        """Resolve max_surge to an absolute count (rounds up for percentages)."""
        return self._resolve(self.max_surge, desired_replicas, round_up=True)

    def resolve_max_unavailable(self, desired_replicas: int) -> int:
        """Resolve max_unavailable to an absolute count (rounds down for percentages)."""
        return self._resolve(self.max_unavailable, desired_replicas, round_up=False)

    @staticmethod
    def _resolve(value: IntOrPercent, total: int, *, round_up: bool) -> int:
        """Convert an IntOrPercent to an absolute replica count.

        For count, returns the value as-is.
        For percent, multiplies by total and rounds up (ceil) or down (floor)
        following Kubernetes rolling-update semantics.
        """
        if value.count is not None:
            return value.count
        result = total * (value.percent or 0.0)
        return math.ceil(result) if round_up else math.floor(result)


class BlueGreenSpec(DeploymentStrategySchema):
    """Specification for blue-green deployment strategy."""

    auto_promote: bool = False
    promote_delay_seconds: int = 0

    def to_rollout_spec(self) -> ReplicaGroupRolloutSpec:
        """The per-group rollout step: blue-green fills a separate group to the goal at creation,
        so there is no in-place surge."""
        return ReplicaGroupRolloutSpec(
            max_surge=IntOrPercent(count=0),
            max_unavailable=IntOrPercent(count=0),
        )

    @override
    def rollout_target(self) -> TargetGroupSpec:
        return TargetGroupSpec(use_primary_group=False, rollout=self.to_rollout_spec())

    @override
    def traffic_step(self, step_input: TrafficStepInput) -> TrafficStep:
        if not self.auto_promote:
            # Manual: hold the current split; the user cuts over by raising the weight to 100.
            return TrafficStep(
                target_traffic_weight=step_input.target_traffic_weight,
                serving_traffic_weight=step_input.serving_traffic_weight,
                completed=step_input.target_traffic_weight >= 100,
            )
        elapsed = (step_input.now - step_input.last_changed_at).total_seconds()
        if elapsed >= self.promote_delay_seconds:
            return TrafficStep(target_traffic_weight=100, serving_traffic_weight=0, completed=True)
        return TrafficStep(
            target_traffic_weight=step_input.target_traffic_weight,
            serving_traffic_weight=step_input.serving_traffic_weight,
            completed=False,
        )


class CanarySpec(DeploymentStrategySchema):
    """Specification for canary deployment strategy."""

    step_weight: int = Field(default=20, ge=1, le=100)
    step_interval_seconds: int = Field(default=0, ge=0)

    def to_rollout_spec(self) -> ReplicaGroupRolloutSpec:
        """The per-group rollout step: canary fills a separate group to the goal at creation,
        so there is no in-place surge."""
        return ReplicaGroupRolloutSpec(
            max_surge=IntOrPercent(count=0),
            max_unavailable=IntOrPercent(count=0),
        )

    @override
    def rollout_target(self) -> TargetGroupSpec:
        return TargetGroupSpec(use_primary_group=False, rollout=self.to_rollout_spec())

    @override
    def traffic_step(self, step_input: TrafficStepInput) -> TrafficStep:
        elapsed = (step_input.now - step_input.last_changed_at).total_seconds()
        if elapsed < self.step_interval_seconds:
            return TrafficStep(
                target_traffic_weight=step_input.target_traffic_weight,
                serving_traffic_weight=step_input.serving_traffic_weight,
                completed=step_input.target_traffic_weight >= 100,
            )
        next_target = min(100, step_input.target_traffic_weight + self.step_weight)
        return TrafficStep(
            target_traffic_weight=next_target,
            serving_traffic_weight=100 - next_target,
            completed=next_target >= 100,
        )
