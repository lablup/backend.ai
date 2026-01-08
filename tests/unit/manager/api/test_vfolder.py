from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.manager.api import vfolder
from ai.backend.manager.api.vfolder import with_vfolder_rows_resolved, with_vfolder_status_checked
from ai.backend.manager.errors.storage import TooManyVFoldersFound, VFolderNotFound
from ai.backend.manager.models.vfolder import (
    VFolderPermissionSetAlias,
    VFolderRow,
    VFolderStatusSet,
)


@pytest.mark.asyncio
async def test_uuid_or_name_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_resolver = AsyncMock()
    monkeypatch.setattr(vfolder, "resolve_vfolder_rows", mock_resolver)

    @with_vfolder_rows_resolved(VFolderPermissionSetAlias.READABLE)  # type: ignore
    async def dummy_handler(request, row):
        return

    mock_request = MagicMock()
    mock_request.match_info = {"name": "8e33ca7f-9aa3-4f59-8bbb-526c212da98b"}
    await dummy_handler(mock_request)
    call = mock_resolver.await_args_list[0]
    assert isinstance(call.args[2], UUID)

    mock_request.match_info = {"name": "hello"}
    await dummy_handler(mock_request)
    call = mock_resolver.await_args_list[1]
    assert isinstance(call.args[2], str)


@pytest.mark.parametrize(
    "vfolder_status",
    [
        VFolderStatusSet.ALL,
        VFolderStatusSet.READABLE,
        VFolderStatusSet.MOUNTABLE,
        VFolderStatusSet.UPDATABLE,
        VFolderStatusSet.DELETABLE,
        VFolderStatusSet.PURGABLE,
        VFolderStatusSet.RECOVERABLE,
        VFolderStatusSet.INACCESSIBLE,
    ],
)
async def test_too_many_vfolders(vfolder_status):
    @with_vfolder_status_checked(vfolder_status)
    async def too_many_vfolders_handler(request, row: VFolderRow):
        return AsyncMock(return_value=web.Response(text="no response"))

    mock_entry = {
        "id": "fake-vfolder-id",
        "host": "fake-vfolder-host",
        "user_email": "fake-user@backend.ai",
        "user": "fake-user",
        "group_name": "fake-group",
        "group": "fake-group-id",
    }
    with pytest.raises(TooManyVFoldersFound):
        await too_many_vfolders_handler(Mock(), [mock_entry, mock_entry])


@pytest.mark.parametrize(
    "vfolder_status",
    [
        VFolderStatusSet.ALL,
        VFolderStatusSet.READABLE,
        VFolderStatusSet.MOUNTABLE,
        VFolderStatusSet.UPDATABLE,
        VFolderStatusSet.DELETABLE,
        VFolderStatusSet.PURGABLE,
        VFolderStatusSet.RECOVERABLE,
        VFolderStatusSet.INACCESSIBLE,
    ],
)
async def test_no_vfolders(vfolder_status):
    @with_vfolder_status_checked(vfolder_status)
    async def no_vfolders_handler(request, row: VFolderRow):
        return AsyncMock(return_value=web.Response(text="no response"))

    with pytest.raises(VFolderNotFound):
        await no_vfolders_handler(Mock(), [])
