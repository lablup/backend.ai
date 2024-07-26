import functools
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.api.utils import set_handler_attr
from ai.backend.manager.api.vfolder import VFolderPermission, VFolderRow


def mock_auth_required(handler):
    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        print("mock_auth_required called")
        return await handler(request, *args, **kwargs)

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped


def mock_server_status_required(allowed_status):
    def decorator(handler):
        @functools.wraps(handler)
        async def wrapped(request, *args, **kwargs):
            print("mock_server_status_required called")
            return await handler(request, *args, **kwargs)

        set_handler_attr(wrapped, "server_status_required", True)
        set_handler_attr(wrapped, "required_server_statuses", allowed_status)
        return wrapped

    return decorator


def mock_with_vfolder_rows_resolved(permission):
    def decorator(handler):
        @functools.wraps(handler)
        async def wrapped(request, *args, **kwargs):
            print("mock_with_vfolder_rows_resolved called")
            return await handler(request, *args, **kwargs)

        return wrapped

    return decorator


def mock_with_vfolder_status_checked(status):
    def decorator(handler):
        @functools.wraps(handler)
        async def wrapped(request, *args, **kwargs):
            print("mock_with_vfolder_status_checked called")
            return await handler(request, *args, **kwargs)

        return wrapped

    return decorator


@pytest.mark.asyncio
@patch("ai.backend.manager.api.auth.auth_required", mock_auth_required)
@patch("ai.backend.manager.api.manager.server_status_required", mock_server_status_required)
@patch("ai.backend.manager.api.vfolder.with_vfolder_rows_resolved", mock_with_vfolder_rows_resolved)
@patch(
    "ai.backend.manager.api.vfolder.with_vfolder_status_checked", mock_with_vfolder_status_checked
)
async def test_get_info_no_user_no_group():
    print("test_get_info_no_user_no_group started")
    # Mock request and row
    request = MagicMock()
    request.match_info = {"name": "test-folder"}
    request["keypair"] = {"access_key": "test-access-key"}
    request["user"] = {"email": "test-user@example.com"}
    request.app = {"_root.context": AsyncMock()}
    request.app["_root.context"].shared_config.get_manager_status = AsyncMock(
        return_value="running"
    )
    request["is_authorized"] = True

    from ai.backend.manager.api.vfolder import get_info

    row: VFolderRow = {
        "id": MagicMock(hex="test-id"),
        "name": "test-folder",
        "host": "test-host",
        "quota_scope_id": MagicMock(),
        "status": "active",
        "created_at": "2024-07-16T00:20:10.759063+00:00",
        "user": None,
        "group": None,
        "is_owner": True,
        "permission": None,
        "usage_mode": "data",
        "cloneable": False,
        "max_size": None,
        "cur_size": 0,
    }

    # Mock storage manager response
    request.app["_root.context"].storage_manager.split_host = MagicMock(
        return_value=("proxy", "volume")
    )

    async def mock_request(*args, **kwargs):
        class MockResponse:
            async def json(self):
                return {"numFiles": 1, "file_count": 4, "used_bytes": 320}

        return (None, MockResponse())

    request.app["_root.context"].storage_manager.request = mock_request
    response = await get_info(request, row)

    assert response.status == 200
    data = await response.json()
    assert data["name"] == "test-folder"
    assert data["id"] == "test-id"
    assert data["host"] == "test-host"
    assert data["quota_scope_id"] == str(row["quota_scope_id"])
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
    print("test_get_info_no_user_no_group finished")
