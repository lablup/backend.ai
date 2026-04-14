from __future__ import annotations

import uuid

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.group.types import GroupData, ProjectType
from ai.backend.manager.data.permission.types import OperationType


def _make_group_data() -> GroupData:
    return GroupData(
        id=uuid.uuid4(),
        name="test-project",
        description=None,
        is_active=True,
        created_at=None,
        modified_at=None,
        integration_name=None,
        domain_name="default",
        total_resource_slots=ResourceSlot(),
        allowed_vfolder_hosts=VFolderHostPermissionMap(),
        dotfiles=b"",
        resource_policy="default",
        type=ProjectType.GENERAL,
        container_registry=None,
    )


class TestGroupDataEntityOperations:
    def test_includes_project_admin_page_read(self) -> None:
        operations = _make_group_data().entity_operations()

        assert RBACElementType.PROJECT_ADMIN_PAGE in operations
        assert set(operations[RBACElementType.PROJECT_ADMIN_PAGE]) == {OperationType.READ}

    def test_admin_resource_entries_unchanged(self) -> None:
        operations = _make_group_data().entity_operations()

        # Sanity check: existing admin entries still receive full admin operations.
        assert set(operations[RBACElementType.VFOLDER]) == OperationType.admin_operations()
        assert set(operations[RBACElementType.USER]) == OperationType.admin_operations()
