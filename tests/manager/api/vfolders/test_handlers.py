import uuid

import pytest

from ai.backend.manager.api.exceptions import InvalidAPIParameters
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
async def test_create_vfolder_validation(
    mock_auth_required, mock_server_status_required, mock_vfolder_service, mock_request
):
    # Given
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)

    # Test: personal vfolder creation
    personal_data = {
        "name": "test-folder",
        "folder_host": "test-host",
        "usage_mode": "general",
        "permission": VFolderPermission.READ_WRITE,
    }
    request = mock_request
    response = await handler.create_vfolder(request, VFolderCreateRequestModel(**personal_data))

    assert isinstance(response, VFolderCreateResponseModel)
    assert response.name == personal_data["name"]
    assert response.ownership_type == VFolderOwnershipType.USER

    # Test: group vfolder creation
    group_data = {**personal_data, "group": str(uuid.uuid4())}
    response = await handler.create_vfolder(request, VFolderCreateRequestModel(**group_data))

    assert isinstance(response, VFolderCreateResponseModel)
    assert response.ownership_type == VFolderOwnershipType.GROUP

    # Test: invalid vfolder name
    invalid_data = {"name": "invalid/name", "folder_host": "test-host"}
    with pytest.raises(InvalidAPIParameters):
        await handler.create_vfolder(request, VFolderCreateRequestModel(**invalid_data))


@pytest.mark.asyncio
async def test_list_vfolders(
    mock_auth_required,
    mock_server_status_required,
    mock_vfolder_handler,
    mock_vfolder_service,
    mock_request,
):
    # Given
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)

    # Test: list all vfolders
    params = {"all": True}
    request = mock_request
    response = await handler.list_vfolders(request, VFolderListRequestModel(**params))

    assert isinstance(response, VFolderListResponseModel)
    assert len(response.root) == 1
    assert response.root[0].name == "test-folder"
    assert response.root[0].user_email == "test@example.com"

    # Test: list with group filter
    group_params = {"all": False, "group_id": str(uuid.uuid4())}
    response = await handler.list_vfolders(request, VFolderListRequestModel(**group_params))

    assert isinstance(response, VFolderListResponseModel)
    assert len(response.root) == 1


@pytest.mark.asyncio
async def test_rename_vfolder(
    mock_auth_required, mock_server_status_required, mock_vfolder_service, mock_request
):
    # Given
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)
    vfolder_id = uuid.uuid4()
    valid_data = {"new_name": "new-folder-name"}
    invalid_data = {"new_name": "invalid/name"}

    # 테스트 분리 할 수 있는 것들 분리 (상태 유지의 가능성 최소화 - 테스트 병렬 실행시)
    # Test: valid rename case
    request = mock_request
    request.match_info = {"vfolder_id": str(vfolder_id)}

    response = await handler.rename_vfolder(request, VFolderRenameRequestModel(**valid_data))

    assert isinstance(response, CreatedResponseModel)
    assert response.status == 201

    # Test: invalid name case
    request.match_info = {"vfolder_id": str(vfolder_id)}

    with pytest.raises(InvalidAPIParameters):
        await handler.rename_vfolder(request, VFolderRenameRequestModel(**invalid_data))


@pytest.mark.asyncio
async def test_delete_vfolder(
    mock_auth_required, mock_server_status_required, mock_vfolder_service, mock_request
):
    # Given
    handler = VFolderHandler(vfolder_service=mock_vfolder_service)
    # Test: valid deletion
    valid_uuid = str(uuid.uuid4())
    valid_data = {"vfolder_id": valid_uuid}
    request = mock_request
    response = await handler.delete_vfolder(
        request=request, params=VFolderDeleteRequestModel(**valid_data)
    )

    assert isinstance(response, NoContentResponseModel)
    assert response.status == 204

    # Test: invalid uuid format
    invalid_data = {"vfolder_id": "not-a-uuid"}
    with pytest.raises(Exception):
        await handler.delete_vfolder(request, VFolderDeleteRequestModel(**invalid_data))
