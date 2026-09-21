"""Reads whose check was hand-written in a resolver are answered by the action gate.

The processor is built from the production wiring with the group validators replaced
by one that refuses everything, so a refusal proves the action went through a gated
factory and names the scope the resolver used to compare by hand.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, override
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.deployment import DeploymentEntityType, DeploymentID
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupID,
)
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.usage_bucket import (
    DomainUsageBucketFieldType,
    ProjectUsageBucketFieldType,
    UserUsageBucketFieldType,
)
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import AtomicBulkActionValidator
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.domain.scopes import (
    ResourceGroupDomainTarget,
)
from ai.backend.manager.models.domain.searchers import DomainSearcher
from ai.backend.manager.models.endpoint.searchers import AutoScalingRuleSearcher
from ai.backend.manager.models.rbac_models.user_role.scopes import RoleRoleAssignmentTarget
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.resource_usage_history.scopes import DomainUsageBucketTarget
from ai.backend.manager.models.resource_usage_history.searchers import DomainUsageBucketSearcher
from ai.backend.manager.models.routing.searchers import RouteInfoSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.models.storage_namespace.scopes import ObjectStorageNamespaceTarget
from ai.backend.manager.models.storage_namespace.searchers import StorageNamespaceSearcher
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.search_auto_scaling_rules import (
    SearchAutoScalingRulesAction,
)
from ai.backend.manager.services.deployment.actions.route.search_routes import SearchRoutesAction
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.domain.actions.scoped_search import (
    ScopedSearchDomainsAction,
)
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.permission_contoller.actions.search_my_role_assignments import (
    ScopedSearchRoleAssignmentsAction,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.resource_usage.actions.search_domain_usage_buckets import (
    SearchDomainUsageBucketsAction,
)
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors
from ai.backend.manager.services.storage_namespace.actions.get_multi import GetNamespacesAction
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors


class _DenyingScopeValidator(ScopeActionValidator):
    def __init__(self) -> None:
        self.seen: list[BaseScopeAction] = []

    @override
    async def validate(self, action: BaseScopeAction, meta: ActionTriggerMeta) -> None:
        self.seen.append(action)
        raise NotEnoughPermission(f"denied at scopes {action.scope_targets()}")


class _DenyingBulkValidator(AtomicBulkActionValidator):
    def __init__(self) -> None:
        self.seen: list[Sequence[EntityIdentifier]] = []

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> None:
        self.seen.append(meta.entity_ids)
        raise NotEnoughPermission(f"denied at entities {meta.entity_ids}")


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


@pytest.fixture
def denying_bulk() -> _DenyingBulkValidator:
    return _DenyingBulkValidator()


@pytest.fixture
def bulk_registry(denying_bulk: _DenyingBulkValidator) -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(atomic_bulk=[denying_bulk]),
            repository=OpsRepository(MagicMock()),
        )
    )


async def test_rg_domain_search_is_answered_for_the_resource_group(
    registry: ProcessorRegistry[Any],
    denying_scope: _DenyingScopeValidator,
    regular_user: UserData,
) -> None:
    processors = DomainProcessors(registry.group(GroupMeta(DomainEntityType())), MagicMock())
    resource_group_id = ResourceGroupID(uuid.uuid4())
    action = ScopedSearchDomainsAction(
        searcher=ScopedSearcher(
            scopes=[ResourceGroupDomainTarget(resource_group_id=resource_group_id)],
            used_by=(),
            searcher=DomainSearcher(pagination=NoPagination(), conditions=[]),
        )
    )

    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await processors.scoped_search.run(action)

    assert [seen.scope_targets() for seen in denying_scope.seen] == [[resource_group_id]]


async def test_route_search_is_answered_for_the_deployment(
    denying_bulk: _DenyingBulkValidator,
    bulk_registry: ProcessorRegistry[Any],
    regular_user: UserData,
) -> None:
    processors = DeploymentProcessors(
        bulk_registry.group(GroupMeta(DeploymentEntityType())), MagicMock()
    )
    deployment_id = DeploymentID(uuid.uuid4())
    action = SearchRoutesAction(
        deployment_ids=[deployment_id],
        searcher=RouteInfoSearcher(pagination=NoPagination(), conditions=[]),
    )

    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await processors.search_routes.run(action)

    assert [list(seen) for seen in denying_bulk.seen] == [[deployment_id]]


async def test_auto_scaling_rule_search_is_answered_for_the_deployment(
    denying_bulk: _DenyingBulkValidator,
    bulk_registry: ProcessorRegistry[Any],
    regular_user: UserData,
) -> None:
    processors = DeploymentProcessors(
        bulk_registry.group(GroupMeta(DeploymentEntityType())), MagicMock()
    )
    deployment_id = DeploymentID(uuid.uuid4())
    action = SearchAutoScalingRulesAction(
        deployment_ids=[deployment_id],
        searcher=AutoScalingRuleSearcher(pagination=NoPagination(), conditions=[]),
    )

    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await processors.search_auto_scaling_rules.run(action)

    assert [list(seen) for seen in denying_bulk.seen] == [[deployment_id]]


async def test_role_assignment_search_is_answered_for_the_role(
    registry: ProcessorRegistry[Any],
    denying_scope: _DenyingScopeValidator,
    regular_user: UserData,
) -> None:
    processors = PermissionControllerProcessors(
        registry.group(GroupMeta(RoleEntityType())),
        registry.group(GroupMeta(UserEntityType())),
        MagicMock(),
    )
    role_id = RoleID(uuid.uuid4())
    action = ScopedSearchRoleAssignmentsAction(
        targets=[RoleRoleAssignmentTarget(role_id=role_id)],
        searcher=RoleAssignmentSearcher(pagination=NoPagination(), conditions=[]),
    )

    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await processors.scoped_search_role_assignments.run(action)

    assert [seen.scope_targets() for seen in denying_scope.seen] == [[role_id]]


async def test_namespace_search_is_answered_for_the_object_storage(
    registry: ProcessorRegistry[Any],
    denying_scope: _DenyingScopeValidator,
    regular_user: UserData,
) -> None:
    processors = StorageNamespaceProcessors(registry.group(GroupMeta(StorageNamespaceEntityType())))
    storage_id = ObjectStorageID(uuid.uuid4())
    action = GetNamespacesAction(
        searcher=ScopedSearcher(
            scopes=[ObjectStorageNamespaceTarget(storage_id=storage_id)],
            used_by=(),
            searcher=StorageNamespaceSearcher(pagination=NoPagination(), conditions=[]),
        )
    )

    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await processors.get_namespaces.run(action)

    assert [seen.scope_targets() for seen in denying_scope.seen] == [[storage_id]]


async def test_domain_usage_bucket_search_is_answered_for_the_resource_group(
    registry: ProcessorRegistry[Any],
    denying_scope: _DenyingScopeValidator,
    regular_user: UserData,
) -> None:
    processors = ResourceUsageProcessors(
        registry.dangling_field_group(
            FieldGroupMeta(DomainUsageBucketFieldType()), DomainUsageBucketData
        ),
        registry.dangling_field_group(
            FieldGroupMeta(ProjectUsageBucketFieldType()), ProjectUsageBucketData
        ),
        registry.dangling_field_group(
            FieldGroupMeta(UserUsageBucketFieldType()), UserUsageBucketData
        ),
    )
    resource_group_id = ResourceGroupID(uuid.uuid4())
    action = SearchDomainUsageBucketsAction(
        targets=[DomainUsageBucketTarget(resource_group_id=resource_group_id)],
        searcher=DomainUsageBucketSearcher(pagination=NoPagination(), conditions=[]),
    )

    with with_user(regular_user), pytest.raises(NotEnoughPermission):
        await processors.search_domain_usage_buckets.run(action)

    assert [seen.scope_targets() for seen in denying_scope.seen] == [[resource_group_id]]
