import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from pydantic import BaseModel

from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderUsageMode,
)
from ai.backend.manager.data.vfolder.dto import UserIdentity
from ai.backend.manager.models import (
    DomainRow,
    GroupRow,
    ProjectResourcePolicyRow,
    ProjectType,
    UserResourcePolicyRow,
    UserRole,
    UserRow,
    UserStatus,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderRow,
)


@pytest.fixture
def mock_authenticated_request():
    mock_request = MagicMock()
    mock_request.__getitem__.side_effect = {
        "user": {
            "uuid": uuid.uuid4(),
            "role": "user",
            "email": "test@email.com",
            "domain_name": "default",
        },
        "keypair": {
            "access_key": "TESTKEY",
            "resource_policy": {"allowed_vfolder_hosts": ["local"]},
        },
    }.get

    vfolder_id = str(uuid.uuid4())
    mock_request.match_info = {"vfolder_id": vfolder_id}
    return mock_request


class TestResponse(BaseModel):
    test: str


@pytest.fixture
def mock_success_response() -> TestResponse:
    return TestResponse(test="response")


@pytest.fixture
async def create_user_resource_policy(
    database_engine: ExtendedAsyncSAEngine,
) -> Callable[[str], Awaitable[str]]:
    async def _create_user_resource_policy(
        name: str,
        max_vfolder_count: int = 0,
        max_quota_scope_size: int = -1,
        max_session_count_per_model_session: int = 5,
        max_customized_image_count: int = 3,
    ) -> str:
        async with database_engine.begin() as conn:
            policy_data = {
                "name": name,
                "max_vfolder_count": max_vfolder_count,
                "max_quota_scope_size": max_quota_scope_size,
                "max_session_count_per_model_session": max_session_count_per_model_session,
                "max_customized_image_count": max_customized_image_count,
            }
            await conn.execute(
                sa.insert(UserResourcePolicyRow)
                .values(policy_data)
                .returning(UserResourcePolicyRow)
            )
            return name

    return _create_user_resource_policy


@pytest.fixture
async def create_project_resource_policy(
    database_engine: ExtendedAsyncSAEngine,
) -> Callable[[str], Awaitable[str]]:
    async def _create_project_resource_policy(
        name: str,
        max_vfolder_count: int = 0,
        max_quota_scope_size: int = -1,
        max_network_count: int = 0,
    ) -> str:
        async with database_engine.begin() as conn:
            policy_data = {
                "name": name,
                "max_vfolder_count": max_vfolder_count,
                "max_quota_scope_size": max_quota_scope_size,
                "max_network_count": max_network_count,
            }
            await conn.execute(
                sa.insert(ProjectResourcePolicyRow)
                .values(policy_data)
                .returning(ProjectResourcePolicyRow)
            )
            return name

    return _create_project_resource_policy


@pytest.fixture
async def create_domain(
    database_engine: ExtendedAsyncSAEngine,
) -> Callable[..., Awaitable[str]]:
    async def _create_domain(name: str = "test-domain") -> str:
        async with database_engine.begin() as conn:
            domain_name = name
            domain_data: dict[str, Any] = {
                "name": domain_name,
                "description": f"Test Domain for {name}",
                "is_active": True,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {
                    "local": [VFolderHostPermission.CREATE],
                },
                "allowed_docker_registries": [],
                "integration_id": None,
            }
            await conn.execute(sa.insert(DomainRow).values(domain_data).returning(DomainRow))
            return domain_name

    return _create_domain


@pytest.fixture
async def create_user_with_role(
    database_engine: ExtendedAsyncSAEngine,
) -> Callable[..., Awaitable[uuid.UUID]]:
    """
    NOTICE: To use 'default' resource policy, you must use `database_fixture` concurrently in test function
    """

    async def _create_user(
        domain_name: str,
        role: UserRole,
        name: str,
        container_uid: Optional[int] = 1000,
        resource_policy_name: str = "default",
    ) -> uuid.UUID:
        async with database_engine.begin() as conn:
            user_id = uuid.uuid4()
            username = name
            user_data = {
                "uuid": user_id,
                "username": username,
                "email": f"{username}@test.com",
                "password": "sample_password",
                "need_password_change": False,
                "full_name": "Sample User",
                "description": "Test user",
                "status": UserStatus.ACTIVE,
                "status_info": None,
                "domain_name": domain_name,
                "role": role,
                "resource_policy": resource_policy_name,
                "totp_activated": False,
                "sudo_session_enabled": False,
                "container_uid": container_uid,
            }
            await conn.execute(sa.insert(UserRow).values(user_data))
            await conn.execute(sa.select(UserRow).where(UserRow.uuid == user_id))
            return user_id

    return _create_user


@pytest.fixture
async def create_identity(
    create_user_with_role: Callable,
) -> Callable[..., Awaitable[tuple[uuid.UUID, UserIdentity]]]:
    """
    NOTICE: To use 'default' resource policy in create_user_with_role, you must use `database_fixture` concurrently in test function
    """

    async def _create_identity(
        domain_name: str, role: UserRole, name: str, resource_policy_name: str = "default"
    ) -> tuple[uuid.UUID, UserIdentity]:
        user_id = await create_user_with_role(domain_name, role, name, resource_policy_name)
        identity = UserIdentity(
            user_uuid=user_id, user_role=role, domain_name=domain_name, user_email="test@email.com"
        )
        return user_id, identity

    return _create_identity


@pytest.fixture
async def create_vfolder(
    database_engine: ExtendedAsyncSAEngine,
) -> Callable[..., Awaitable[uuid.UUID]]:
    async def _create_vfolder(
        domain_name: str,
        user_id: Optional[uuid.UUID],
        group_id: Optional[uuid.UUID],
        name: str,
    ) -> uuid.UUID:
        assert (user_id is not None) or (group_id is not None)
        quota_scope_type = QuotaScopeType.USER if user_id else QuotaScopeType.PROJECT
        scope_id = user_id if user_id is not None else group_id
        assert scope_id is not None
        quota_scope_id = str(QuotaScopeID(quota_scope_type, scope_id))
        async with database_engine.begin() as conn:
            vfolder_id = uuid.uuid4()
            vfolder_data = {
                "id": vfolder_id,
                "host": "local",
                "name": name,
                "domain_name": domain_name,
                "user": user_id,
                "group": group_id,
                "quota_scope_id": quota_scope_id,
                "usage_mode": VFolderUsageMode.GENERAL,
                "permission": VFolderPermission.READ_WRITE,
                "ownership_type": VFolderOwnershipType.USER
                if user_id
                else VFolderOwnershipType.GROUP,
                "status": VFolderOperationStatus.READY,
                "max_files": 1000,
                "max_size": 1024 * 1024,
                "created_at": datetime.now(timezone.utc),
                "last_used": None,
                "cloneable": True,
            }
            await conn.execute(sa.insert(VFolderRow).values(vfolder_data))
            await conn.execute(sa.select(VFolderRow).where(VFolderRow.id == vfolder_id))
            return vfolder_id

    return _create_vfolder


@pytest.fixture
async def create_group(
    database_engine: ExtendedAsyncSAEngine,
) -> Callable[..., Awaitable[uuid.UUID]]:
    """
    NOTICE: To use 'default' resource policy, you must use `database_fixture` concurrently in test function
    """

    async def _create_group(
        domain_name: str,
        name: str,
        type: ProjectType = ProjectType.GENERAL,
        resource_policy_name: str = "default",
    ) -> uuid.UUID:
        async with database_engine.begin() as conn:
            group_id = uuid.uuid4()
            group_data = {
                "id": group_id,
                "name": name,
                "description": "Test group",
                "is_active": True,
                "domain_name": domain_name,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "resource_policy": resource_policy_name,
                "type": type,
            }
            await conn.execute(sa.insert(GroupRow).values(group_data))
            await conn.execute(sa.select(GroupRow).where(GroupRow.id == group_id))
            return group_id

    return _create_group
