from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.session_template import (
    SESSION_TEMPLATE_ENTITY_TYPE,
    SessionTemplateID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class TemplateAction(BaseSingleEntityAction):
    """Base for an operation on one session template."""

    template_id: SessionTemplateID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.template_id


@dataclass
class TemplateProjectScopeAction(BaseScopeAction):
    """Base for a template operation that names no template yet: a create, or a read
    of what a project holds."""

    requesting_project: ProjectID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_TEMPLATE_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.requesting_project),)


@dataclass
class TemplateUserScopeAction(BaseScopeAction):
    """Base for a read of the templates one user holds."""

    user_uuid: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_TEMPLATE_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_uuid),)


@dataclass
class TemplateScopeActionResult(BaseScopeActionResult):
    """A template read names no entity: the caller named a scope."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
