import uuid
from typing import Sequence
from unittest.mock import MagicMock, Mock

import pytest
from aiohttp import web

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.api import auth, manager
from ai.backend.manager.api.exceptions import InvalidAPIParameters
from ai.backend.manager.api.utils import set_handler_attr
from ai.backend.manager.api.vfolders.protocols import VFolderServiceProtocol
from ai.backend.manager.api.vfolders.types import (
    Keypair,
    UserIdentity,
    VFolderCreateRequirements,
    VFolderList,
    VFolderListItem,
    VFolderMetadata,
)
from ai.backend.manager.models import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)


@pytest.fixture
def mock_request():
    request = MagicMock(spec=web.Request)
    request.get.side_effect = lambda key, default=None: {
        "is_authorized": True,
        "is_admin": True,
    }.get(key, default)
    return request


@pytest.fixture
async def mock_auth_required(monkeypatch):
    async def mock_decorator(handler):
        async def wrapped(request, *args, **kwargs):
            return await handler(request, *args, **kwargs)

        set_handler_attr(wrapped, "auth_required", True)
        set_handler_attr(wrapped, "auth_scope", "user")
        return wrapped

    monkeypatch.setattr(auth, "auth_required", mock_decorator)


@pytest.fixture
async def mock_server_status_required(monkeypatch):
    def mock_decorator(allowed_status):
        async def inner(handler):
            async def wrapped(request, *args, **kwargs):
                return await handler(request, *args, **kwargs)

            set_handler_attr(wrapped, "server_status_required", True)
            set_handler_attr(wrapped, "required_server_statuses", allowed_status)
            return wrapped

        return inner

    monkeypatch.setattr(manager, "server_status_required", mock_decorator)


@pytest.fixture
def test_user_identity():
    return UserIdentity(user_uuid=uuid.uuid4, user_role="user", domain_name="default")


@pytest.fixture
def test_keypair():
    return Keypair(access_key="test-key", resource_policy={})


@pytest.fixture
def mock_vfolder_service():
    class MockVFolderService(VFolderServiceProtocol):
        async def create_vfolder_in_personal(
            self,
            user_identity: UserIdentity,
            keypair: Keypair,
            vfolder_create_requirements: VFolderCreateRequirements,
        ) -> VFolderMetadata:
            return VFolderMetadata(
                id="test-id",
                name="test-folder",
                quota_scope_id=Mock(spec=QuotaScopeID, side_effect=lambda: "test-quota-scope-id"),
                host="test-host",
                usage_mode=VFolderUsageMode.GENERAL,
                created_at="2024-01-16",
                permission=VFolderPermission.READ_WRITE,
                max_size=0,
                creator="test@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user="test-user",
                group=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )

        async def create_vfolder_in_group(
            self,
            user_identity: UserIdentity,
            keypair: Keypair,
            vfolder_create_requirements: VFolderCreateRequirements,
        ) -> VFolderMetadata:
            return VFolderMetadata(
                id="test-id",
                name="test-folder",
                quota_scope_id=Mock(spec=QuotaScopeID, side_effect=lambda: "test-quota-scope-id"),
                host="test-host",
                usage_mode=VFolderUsageMode.GENERAL,
                created_at="2024-01-16",
                permission=VFolderPermission.READ_WRITE,
                max_size=0,
                creator="test@example.com",
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group="test-group",
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )

        async def get_vfolders(self, user_identity: UserIdentity) -> VFolderList:
            return VFolderList(
                entries=[
                    VFolderListItem(
                        id="test-id",
                        name="test-folder",
                        quota_scope_id=Mock(
                            spec=QuotaScopeID, side_effect=lambda: "test-quota-scope-id"
                        ),
                        host="test-host",
                        usage_mode=VFolderUsageMode.GENERAL,
                        created_at="2024-01-16",
                        permission=VFolderPermission.READ_WRITE,
                        max_size=0,
                        creator="test@example.com",
                        ownership_type=VFolderOwnershipType.USER,
                        user="test-user",
                        group=None,
                        cloneable=False,
                        status=VFolderOperationStatus.READY,
                        is_owner=True,
                        user_email="test@example.com",
                        group_name="",
                        type="user",
                        max_files=1000,
                        cur_size=0,
                    )
                ]
            )

        async def rename_vfolder(
            self, user_identity: UserIdentity, vfolder_id: uuid.UUID, new_name: str
        ) -> None:
            if "?" in new_name:
                raise InvalidAPIParameters("Invalid folder name")

        async def delete_vfolder(
            self,
            vfolder_id: uuid.UUID,
            user_identity: UserIdentity,
            allowed_vfolder_types: Sequence[str],
            keypair: Keypair,
        ) -> None:
            pass

    return MockVFolderService()
