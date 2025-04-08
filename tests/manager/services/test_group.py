import uuid
from datetime import datetime

import pytest

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.services.groups.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.groups.processors import GroupProcessors
from ai.backend.manager.services.groups.types import GroupCreator, GroupData

from .test_utils import TestScenario


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Create a group",
            CreateGroupAction(
                input=GroupCreator(
                    name="test-create-group",
                    domain_name="default",
                    type=ProjectType.GENERAL,
                    description="Test group",
                    is_active=True,
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts={},
                    integration_id=None,
                    resource_policy=None,
                    container_registry=None,
                ),
            ),
            CreateGroupActionResult(
                data=GroupData(
                    id=uuid.UUID("676fb4e3-17d3-48e9-91ca-4c94cde32a46"),
                    name="test-create-group",
                    description="Test group",
                    is_active=True,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    integration_id=None,
                    domain_name="default",
                    total_resource_slots=ResourceSlot.from_user_input({}, None),
                    allowed_vfolder_hosts=VFolderHostPermissionMap({}),
                    dotfiles=b"",
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                    container_registry={},
                ),
                success=True,
            ),
        ),
        TestScenario.success(
            "Create a group with duplicated name, return none",
            CreateGroupAction(
                input=GroupCreator(
                    name="test-create-group-duplicated",
                    domain_name="default",
                    type=None,
                    description=None,
                    is_active=None,
                    total_resource_slots=None,
                    allowed_vfolder_hosts=None,
                    integration_id=None,
                    resource_policy=None,
                    container_registry=None,
                ),
            ),
            CreateGroupActionResult(
                data=None,
                success=False,
            ),
        ),
    ],
)
async def test_create_group(
    processors: GroupProcessors,
    test_scenario: TestScenario[CreateGroupAction, CreateGroupActionResult],
) -> None:
    await test_scenario.test(processors.create_group.wait_for_complete)
