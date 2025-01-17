from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.manager.api import vfolder
from ai.backend.manager.api.vfolder import with_vfolder_rows_resolved
from ai.backend.manager.models.vfolder import VFolderPermissionSetAlias


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
