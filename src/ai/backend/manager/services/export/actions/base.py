"""Base action classes for export operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult


@dataclass(frozen=True)
class ExportAction(BaseGlobalAction):
    """Base for an export that spans the installation."""


@dataclass(frozen=True)
class ExportUserScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one user."""

    user_uuid: UserID

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.user_uuid,)


@dataclass(frozen=True)
class ExportProjectScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one project."""

    project_id: ProjectID

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.project_id,)


@dataclass(frozen=True)
class ExportDomainScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one domain."""

    domain_id: DomainID
    domain_name: str

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.domain_id,)


@dataclass(frozen=True)
class ExportScopeActionResult(BaseScopeActionResult):
    """An export names no entity: what it wrote is a file, not a row."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
