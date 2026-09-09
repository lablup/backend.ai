"""Reads whose check was hand-written in a resolver are answered by the action gate.

The processor is built from the production wiring with the group validators replaced
by one that refuses everything, so a refusal proves the action went through a gated
factory and names the scope the resolver used to compare by hand.
"""

from __future__ import annotations

import uuid
from typing import Any, override
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_SCOPE_TYPE,
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.domain.searchers import DomainSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.domain.actions.scoped_search import (
    ResourceGroupDomainScopeItem,
    ScopedSearchDomainsAction,
)
from ai.backend.manager.services.domain.processors import DomainProcessors


class _DenyingScopeValidator(ScopeActionValidator):
    def __init__(self) -> None:
        self.seen: list[BaseScopeAction] = []

    @override
    async def validate(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        self.seen.append(action)
        raise NotEnoughPermission(f"denied at scopes {action.scope_targets()}")


@pytest.fixture
def regular_user() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture
def denying_scope() -> _DenyingScopeValidator:
    return _DenyingScopeValidator()


@pytest.fixture
def registry(denying_scope: _DenyingScopeValidator) -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(scope=[denying_scope]),
            repository=OpsRepository(MagicMock()),
        )
    )


async def test_rg_domain_search_is_answered_for_the_resource_group(
    registry: ProcessorRegistry[Any],
    denying_scope: _DenyingScopeValidator,
    regular_user: UserData,
) -> None:
    processors = DomainProcessors(registry.group(GroupMeta(DomainEntityType())), MagicMock(), [])
    resource_group_id = ResourceGroupID(uuid.uuid4())
    action = ScopedSearchDomainsAction(
        items=[ResourceGroupDomainScopeItem(resource_group_id=resource_group_id)],
        searcher=DomainSearcher(pagination=NoPagination(), conditions=[]),
    )

    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await processors.scoped_search.run(action)

    assert [seen.scope_targets() for seen in denying_scope.seen] == [
        [ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=resource_group_id)]
    ]
