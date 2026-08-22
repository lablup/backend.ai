"""Base action classes for scheduling history operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_SCOPE_TYPE, DeploymentID
from ai.backend.common.data.entity.session import SESSION_SCOPE_TYPE, SessionID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult


@dataclass
class SchedulingHistoryAction(BaseGlobalAction):
    """Base for a history read that spans the installation."""


@dataclass
class SessionSchedulingHistoryAction(BaseScopeAction):
    """Base for a history read bounded by one session."""

    session_id: SessionID

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=SESSION_SCOPE_TYPE, scope_id=self.session_id),)


@dataclass
class DeploymentSchedulingHistoryAction(BaseScopeAction):
    """Base for a history read bounded by one deployment."""

    deployment_id: DeploymentID

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DEPLOYMENT_SCOPE_TYPE, scope_id=self.deployment_id),)


@dataclass
class SchedulingHistoryScopeActionResult(BaseScopeActionResult):
    """A history read names no entity: what came back is a record, not a row the
    caller can act on."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


_ = EntityType
