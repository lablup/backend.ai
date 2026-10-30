"""The usage bucket targets are all answered for at the resource group they name."""

from __future__ import annotations

import uuid

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.models.resource_usage_history.scopes import (
    DomainUsageBucketTarget,
    ProjectUsageBucketTarget,
    UserUsageBucketTarget,
)

RESOURCE_GROUP_ID = ResourceGroupID(uuid.uuid4())
PROJECT_ID = uuid.uuid4()
USER_UUID = uuid.uuid4()


def test_domain_target_is_read_for_the_resource_group() -> None:
    target = DomainUsageBucketTarget(resource_group_id=RESOURCE_GROUP_ID, domain_name="default")
    assert target.scope_id() == RESOURCE_GROUP_ID


def test_project_target_is_read_for_the_resource_group() -> None:
    target = ProjectUsageBucketTarget(
        resource_group_id=RESOURCE_GROUP_ID, domain_name="default", project_id=PROJECT_ID
    )
    assert target.scope_id() == RESOURCE_GROUP_ID


def test_user_target_is_read_for_the_resource_group() -> None:
    target = UserUsageBucketTarget(
        resource_group_id=RESOURCE_GROUP_ID,
        domain_name="default",
        project_id=PROJECT_ID,
        user_uuid=USER_UUID,
    )
    assert target.scope_id() == RESOURCE_GROUP_ID
