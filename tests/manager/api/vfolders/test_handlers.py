import uuid
from typing import Any

import pytest
from pydantic_core._pydantic_core import ValidationError

from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.api.vfolders.handlers import VFolderHandler
from ai.backend.manager.api.vfolders.types import (
    CreatedResponseModel,
    NoContentResponseModel,
    VFolderCreateRequestModel,
    VFolderCreateResponseModel,
    VFolderDeleteRequestModel,
    VFolderListRequestModel,
    VFolderListResponseModel,
    VFolderRenameRequestModel,
)
from ai.backend.manager.models import (
    VFolderOwnershipType,
    VFolderPermission,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "folder_data, expected_ownership",
    [
        (
            {
                "name": "test-folder",
                "folder_host": "test-host",
                "usage_mode": VFolderUsageMode.GENERAL,
                "permission": VFolderPermission.READ_WRITE,
            },
            VFolderOwnershipType.USER,
        ),
        (
            {
                "name": "test-folder",
                "folder_host": "test-host",
                "usage_mode": VFolderUsageMode.GENERAL,
                "permission": VFolderPermission.READ_WRITE,
                "group": str(uuid.uuid4()),
            },
            VFolderOwnershipType.GROUP,
        ),
    ],
)
async def test_create_vfolder_success(
    mock_vfolder_service,
    mock_authenticated_request,
    folder_data: dict[str, Any],
    expected_ownership: VFolderOwnershipType,
):
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)
    response = await handler.create_vfolder(
        mock_authenticated_request, VFolderCreateRequestModel(**folder_data)
    )

    assert isinstance(response, VFolderCreateResponseModel)
    assert response.name == folder_data["name"]
    assert response.ownership_type == expected_ownership


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_data",
    [
        {"name": ".bashrc", "folder_host": "test-host"},  # matches ^\.[a-z0-9]+rc$ pattern
        {
            "name": ".python_profile",
            "folder_host": "test-host",
        },  # matches ^\.[a-z0-9]+_profile$ pattern
        {"name": "test" * 50, "folder_host": "test-host"},  # exceeds 64 char limit
        {"name": "/etc", "folder_host": "test-host"},  # in RESERVED_VFOLDERS
        {"name": "/tmp", "folder_host": "test-host"},
    ],
)
async def test_create_vfolder_invalid_input(
    mock_vfolder_service,
    mock_authenticated_request,
    invalid_data: dict[str, Any],
):
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)
    with pytest.raises(ValidationError):
        await handler.create_vfolder(
            mock_authenticated_request, VFolderCreateRequestModel(**invalid_data)
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "list_params,expected_count",
    [
        ({"all": True}, 1),
        ({"all": False, "group_id": str(uuid.uuid4())}, 1),
        ({"all": False, "owner_user_email": "test@test.com"}, 1),
    ],
)
async def test_list_vfolders(
    mock_vfolder_service,
    mock_authenticated_request,
    list_params: dict[str, Any],
    expected_count: int,
):
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)
    response = await handler.list_vfolders(
        mock_authenticated_request, VFolderListRequestModel(**list_params)
    )

    assert isinstance(response, VFolderListResponseModel)
    assert len(response.root) == expected_count
    if response.root:
        assert response.root[0].user_email == "test@test.com"


@pytest.mark.asyncio
async def test_rename_vfolder_success(
    mock_vfolder_service,
    mock_authenticated_request,
):
    mock_request = mock_authenticated_request
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)

    response = await handler.rename_vfolder(
        mock_request,
        VFolderRenameRequestModel(new_name="new-folder-name"),
    )

    assert isinstance(response, CreatedResponseModel)
    assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_name",
    [
        ".bashrc",  # matches ^\.[a-z0-9]+rc$ pattern
        ".bash_profile",  # matches ^\.[a-z0-9]+_profile$ pattern
        ".python_profile",  # matches ^\.[a-z0-9]+_profile$ pattern
        "test" * 50,  # exceeds 64 char limit
        "/etc",  # in RESERVED_VFOLDERS
    ],
)
async def test_rename_vfolder_invalid_name(
    mock_vfolder_service,
    mock_authenticated_request,
    invalid_name: str,
):
    mock_request = mock_authenticated_request
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)

    with pytest.raises(ValidationError):
        await handler.rename_vfolder(
            mock_request,
            VFolderRenameRequestModel(new_name=invalid_name),
        )


@pytest.mark.asyncio
async def test_delete_vfolder_success(
    mock_vfolder_service,
    mock_authenticated_request,
):
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)
    valid_uuid = str(uuid.uuid4())

    response = await handler.delete_vfolder(
        mock_authenticated_request,
        VFolderDeleteRequestModel(vfolder_id=valid_uuid),
    )

    assert isinstance(response, NoContentResponseModel)
    assert response.status_code == 204


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_id",
    [
        ".bashrc",  # matches ^\.[a-z0-9]+rc$ pattern
        ".bash_profile",  # matches ^\.[a-z0-9]+_profile$ pattern
        ".python_profile",  # matches ^\.[a-z0-9]+_profile$ pattern
        "test" * 50,  # exceeds 64 char limit
        "/etc",  # in RESERVED_VFOLDERS
    ],
)
async def test_delete_vfolder_invalid_id(
    mock_vfolder_service,
    mock_authenticated_request,
    invalid_id: uuid.UUID,
):
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)

    with pytest.raises(ValidationError):
        await handler.delete_vfolder(
            mock_authenticated_request,
            VFolderDeleteRequestModel(vfolder_id=invalid_id),
        )
