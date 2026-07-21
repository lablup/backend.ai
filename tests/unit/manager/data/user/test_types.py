from __future__ import annotations

import uuid

import pytest

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import OperationType
from ai.backend.manager.data.user.types import UserData


@pytest.fixture
def user_data() -> UserData:
    user_id = uuid.uuid4()
    return UserData(
        id=user_id,
        uuid=user_id,
        username="test-user",
        email="test-user@example.com",
        need_password_change=False,
        full_name=None,
        description=None,
        is_active=True,
        status="active",
        status_info=None,
        created_at=None,
        modified_at=None,
        domain_name="default",
        role=None,
        resource_policy="default",
        allowed_client_ip=None,
        totp_activated=False,
        totp_activated_at=None,
        sudo_session_enabled=False,
        main_access_key=None,
        container_uid=None,
        container_main_gid=None,
        container_gids=None,
        integration_name=None,
    )


class TestUserDataEntityOperations:
    def test_includes_kernel_history_read(self, user_data: UserData) -> None:
        operations = user_data.entity_operations()

        assert RBACElementType.KERNEL_HISTORY in operations
        assert set(operations[RBACElementType.KERNEL_HISTORY]) == {OperationType.READ}

    def test_owner_resource_entries_unchanged(self, user_data: UserData) -> None:
        operations = user_data.entity_operations()

        assert set(operations[RBACElementType.SESSION]) == OperationType.owner_operations()
        assert set(operations[RBACElementType.USER]) == (
            OperationType.owner_operations() - {OperationType.CREATE}
        )
