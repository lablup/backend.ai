"""The usage bucket scope items authorize and restrict against the same resource group."""

from __future__ import annotations

import uuid

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.models.resource_usage_history.scopes import (
    DomainUsageBucketOperationScope,
    ProjectUsageBucketOperationScope,
    UserUsageBucketOperationScope,
)
from ai.backend.manager.services.resource_usage.actions.scope_items import (
    DomainUsageBucketScopeItem,
    ProjectUsageBucketScopeItem,
    UserUsageBucketScopeItem,
)

RESOURCE_GROUP_ID = ResourceGroupID(uuid.uuid4())
PROJECT_ID = uuid.uuid4()
USER_UUID = uuid.uuid4()


def test_domain_item_is_read_for_the_resource_group() -> None:
    item = DomainUsageBucketScopeItem(resource_group_id=RESOURCE_GROUP_ID, domain_name="default")
    assert item.scope_ref() == RESOURCE_GROUP_ID
    assert item.operation_scope() == DomainUsageBucketOperationScope(
        resource_group_id=RESOURCE_GROUP_ID, domain_name="default"
    )


def test_project_item_is_read_for_the_resource_group() -> None:
    item = ProjectUsageBucketScopeItem(
        resource_group_id=RESOURCE_GROUP_ID, domain_name="default", project_id=PROJECT_ID
    )
    assert item.scope_ref() == RESOURCE_GROUP_ID
    assert item.operation_scope() == ProjectUsageBucketOperationScope(
        resource_group_id=RESOURCE_GROUP_ID, domain_name="default", project_id=PROJECT_ID
    )


def test_user_item_is_read_for_the_resource_group() -> None:
    item = UserUsageBucketScopeItem(
        resource_group_id=RESOURCE_GROUP_ID,
        domain_name="default",
        project_id=PROJECT_ID,
        user_uuid=USER_UUID,
    )
    assert item.scope_ref() == RESOURCE_GROUP_ID
    assert item.operation_scope() == UserUsageBucketOperationScope(
        resource_group_id=RESOURCE_GROUP_ID,
        domain_name="default",
        project_id=PROJECT_ID,
        user_uuid=USER_UUID,
    )
