"""Base action classes for export operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE, DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.export import EXPORT_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult


@dataclass
class ExportAction(BaseGlobalAction):
    """Base for an export that spans the installation."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EXPORT_ENTITY_TYPE


@dataclass
class ExportUserScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one user."""

    user_uuid: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EXPORT_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_uuid),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (USER_ENTITY_TYPE,)


@dataclass
class ExportProjectScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one project."""

    project_id: ProjectID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EXPORT_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE,)


@dataclass
class ExportDomainScopeAction(BaseScopeAction):
    """Base for an export of what belongs to one domain."""

    domain_id: DomainID
    domain_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EXPORT_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.domain_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (DOMAIN_ENTITY_TYPE,)


@dataclass
class ExportScopeActionResult(BaseScopeActionResult):
    """An export names no entity: what it wrote is a file, not a row."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
