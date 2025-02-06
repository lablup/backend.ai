import uuid
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.api.vfolders.dtos import (
    Keypair,
    UserIdentity,
    VFolderCreateRequirements,
    VFolderList,
    VFolderListItem,
    VFolderMetadata,
)
from ai.backend.manager.api.vfolders.handlers import VFolderServiceProtocol
from ai.backend.manager.models import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
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


@pytest.fixture
def mock_vfolder_service():
    return MockVFolderService()


class MockVFolderService(VFolderServiceProtocol):
    async def create_vfolder_in_personal(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_create_requirements: VFolderCreateRequirements,
    ) -> VFolderMetadata:
        return VFolderMetadata(
            id=str(uuid.uuid4()),
            name=vfolder_create_requirements.name,
            quota_scope_id=QuotaScopeID(QuotaScopeType.USER, uuid.uuid4()),
            host="local",
            usage_mode=vfolder_create_requirements.usage_mode,
            created_at=datetime.now().isoformat(),
            permission=vfolder_create_requirements.permission,
            max_size=0,
            creator=str(user_identity.user_uuid),
            ownership_type=VFolderOwnershipType.USER,
            user=str(user_identity.user_uuid),
            group=None,
            cloneable=vfolder_create_requirements.cloneable,
            status=VFolderOperationStatus.READY,
        )

    async def create_vfolder_in_group(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_create_requirements: VFolderCreateRequirements,
    ) -> VFolderMetadata:
        return VFolderMetadata(
            id=str(uuid.uuid4()),
            name=vfolder_create_requirements.name,
            quota_scope_id=QuotaScopeID(QuotaScopeType.USER, uuid.uuid4()),
            host="local",
            usage_mode=vfolder_create_requirements.usage_mode,
            created_at=datetime.now().isoformat(),
            permission=vfolder_create_requirements.permission,
            max_size=0,
            creator=str(user_identity.user_uuid),
            ownership_type=VFolderOwnershipType.GROUP,
            user=None,
            group=str(vfolder_create_requirements.group_id),
            cloneable=vfolder_create_requirements.cloneable,
            status=VFolderOperationStatus.READY,
        )

    async def get_vfolders(
        self, user_identity: UserIdentity, group_id: Optional[uuid.UUID]
    ) -> VFolderList:
        test_vfolder = VFolderListItem(
            id=str(uuid.uuid4()),
            name="test-folder",
            quota_scope_id=str(uuid.uuid4()),
            host="local",
            usage_mode=VFolderUsageMode.GENERAL,
            created_at=datetime.now().isoformat(),
            permission=VFolderPermission.READ_WRITE,
            max_size=0,
            creator=str(user_identity.user_uuid),
            ownership_type=VFolderOwnershipType.USER,
            user=str(user_identity.user_uuid),
            group=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
            is_owner=True,
            user_email="test@test.com",
            group_name="test-group",
            type="user",
            max_files=1000,
            cur_size=0,
        )
        return VFolderList(entries=[test_vfolder])

    async def rename_vfolder(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_id: uuid.UUID,
        new_name: str,
    ) -> None:
        pass

    async def delete_vfolder(
        self,
        vfolder_id: str,
        user_identity: UserIdentity,
        keypair: Keypair,
    ) -> None:
        pass
