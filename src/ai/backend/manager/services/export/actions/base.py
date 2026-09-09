"""Base action classes for export operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.export import ExportEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult


@dataclass
class ExportAction(BaseGlobalAction):
    """Base for an export that spans the installation."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ExportEntityType()


@dataclass
class ExportUserScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one user."""

    user_uuid: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ExportEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.user_uuid,)


@dataclass
class ExportProjectScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one project."""

    project_id: ProjectID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ExportEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.project_id,)


@dataclass
class ExportDomainScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one domain."""

    domain_id: DomainID
    domain_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ExportEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.domain_id,)


@dataclass
class ExportScopeActionResult(BaseScopeActionResult):
    """An export names no entity: what it wrote is a file, not a row."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
