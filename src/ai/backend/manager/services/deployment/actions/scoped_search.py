"""Deployment search over the scopes deployments are reachable from."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.models.endpoint.scopes import DeploymentTarget
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)

__all__ = (
    "ScopedSearchDeploymentsAction",
    "ScopedSearchDeploymentsActionResult",
)


@dataclass
class ScopedSearchDeploymentsAction(DeploymentScopeAction):
    """Page through the deployments the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    targets: Sequence[DeploymentTarget]
    querier: BatchQuerier

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_deployments"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ScopedSearchDeploymentsActionResult(DeploymentScopeActionResult):
    data: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
