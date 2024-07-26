from unittest.mock import MagicMock

import pytest
from backend.manager.api.vfolder import VFolderPermission, VFolderRow, get_info


@pytest.mark.asyncio
async def test_get_info():
    # Mock request and row
    request = MagicMock()
    request.match_info = {"name": "test-folder"}
    request["keypair"] = {"access_key": "test-access-key"}
    request["user"] = {"email": "test-user@example.com"}
    request.app = {"_root.context": MagicMock()}

    row = VFolderRow(
        id=MagicMock(hex="test-id"),
        name="test-folder",
        host="test-host",
        quota_scope_id=MagicMock(),
        status="active",
        created_at="2024-07-16T00:20:10.759063+00:00",
        user=None,
        group=None,
        is_owner=True,
        permission=None,
        usage_mode="data",
        cloneable=False,
        max_size=None,
        cur_size=0,
    )

    # Mock storage manager response
    request.app["_root.context"].storage_manager.split_host = MagicMock(
        return_value=("proxy", "volume")
    )

    async def mock_request(*args, **kwargs):
        class MockResponse:
            async def json(self):
                return {"file_count": 4, "used_bytes": 320}

        return (None, MockResponse())

    request.app["_root.context"].storage_manager.request = mock_request

    response = await get_info(request, row)

    assert response.status == 200
    data = await response.json()
    assert data["name"] == "test-folder"
    assert data["id"] == "test-id"
    assert data["host"] == "test-host"
    assert data["quota_scope_id"] == str(row.quota_scope_id)
    assert data["status"] == "active"
    assert data["num_files"] == 4
    assert data["used_bytes"] == 320
    assert data["created_at"] == "2024-07-16T00:20:10.759063+00:00"
    assert data["last_used"] == "2024-07-16T00:20:10.759063+00:00"
    assert data["user"] is None
    assert data["group"] is None
    assert data["type"] == "group"
    assert data["is_owner"] is True
    assert data["permission"] == VFolderPermission.OWNER_PERM
    assert data["usage_mode"] == "data"
    assert data["cloneable"] is False
    assert data["max_size"] is None
    assert data["cur_size"] == 0


@pytest.mark.asyncio
async def test_get_info_with_user_and_group():
    # Mock request and row
    request = MagicMock()
    request.match_info = {"name": "test-folder"}
    request["keypair"] = {"access_key": "test-access-key"}
    request["user"] = {"email": "test-user@example.com"}
    request.app = {"_root.context": MagicMock()}

    row = VFolderRow(
        id=MagicMock(hex="test-id"),
        name="test-folder",
        host="test-host",
        quota_scope_id=MagicMock(),
        status="active",
        created_at="2024-07-16T00:20:10.759063+00:00",
        user="test-user",
        group="test-group",
        is_owner=True,
        permission=None,
        usage_mode="data",
        cloneable=False,
        max_size=None,
        cur_size=0,
    )

    # Mock storage manager response
    request.app["_root.context"].storage_manager.split_host = MagicMock(
        return_value=("proxy", "volume")
    )

    async def mock_request(*args, **kwargs):
        class MockResponse:
            async def json(self):
                return {"file_count": 4, "used_bytes": 320}

        return (None, MockResponse())

    request.app["_root.context"].storage_manager.request = mock_request

    response = await get_info(request, row)

    assert response.status == 200
    data = await response.json()
    assert data["name"] == "test-folder"
    assert data["id"] == "test-id"
    assert data["host"] == "test-host"
    assert data["quota_scope_id"] == str(row.quota_scope_id)
    assert data["status"] == "active"
    assert data["num_files"] == 4
    assert data["used_bytes"] == 320
    assert data["created_at"] == "2024-07-16T00:20:10.759063+00:00"
    assert data["last_used"] == "2024-07-16T00:20:10.759063+00:00"
    assert data["user"] == "test-user"
    assert data["group"] == "test-group"
    assert data["type"] == "user"
    assert data["is_owner"] is True
    assert data["permission"] == VFolderPermission.OWNER_PERM
    assert data["usage_mode"] == "data"
    assert data["cloneable"] is False
    assert data["max_size"] is None
    assert data["cur_size"] == 0
