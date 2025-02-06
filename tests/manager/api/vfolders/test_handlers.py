# import json
# import uuid
# from typing import Any
# from unittest.mock import AsyncMock, MagicMock, Mock, create_autospec

# from pydantic import BaseModel
# import pytest

# from ai.backend.common.api_handlers import APIResponse
# from ai.backend.common.dto.manager.dto import VFolderPermissionDTO
# from ai.backend.common.exception import InvalidAPIParameters
# from ai.backend.common.types import VFolderUsageMode
# from ai.backend.manager.api.vfolders.handlers import VFolderHandler, VFolderServiceProtocol
# from ai.backend.manager.data.vfolder.dto import UserIdentity
# from ai.backend.manager.models import (
#     VFolderOwnershipType,
# )


# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "folder_data, expected_ownership",
#     [
#         (
#             {
#                 "name": "test-folder",
#                 "folder_host": "test-host",
#                 "usage_mode": VFolderUsageMode.GENERAL,
#                 "permission": VFolderPermissionDTO.READ_WRITE,
#             },
#             VFolderOwnershipType.USER,
#         ),
#         (
#             {
#                 "name": "test-folder",
#                 "folder_host": "test-host",
#                 "usage_mode": VFolderUsageMode.GENERAL,
#                 "permission": VFolderPermissionDTO.READ_WRITE,
#                 "group": str(uuid.uuid4()),
#             },
#             VFolderOwnershipType.GROUP,
#         ),
#     ],
# )
# async def test_create_vfolder_success(
#     mock_authenticated_request,
#     mock_success_response,
#     folder_data: dict[str, Any],
#     expected_ownership: VFolderOwnershipType,
# ):
#     mock_authenticated_request.can_read_body = True
#     mock_authenticated_request.json = AsyncMock(return_value=folder_data)
#     # mock service
#     svc = AsyncMock(VFolderServiceProtocol)
#     created_vfolder_item = MagicMock()
#     created_vfolder_item.to_vfolder_create_response.return_value = mock_success_response
#     match expected_ownership:
#         case VFolderOwnershipType.USER:
#             svc.create_vfolder_in_personal.return_value = created_vfolder_item
#         case VFolderOwnershipType.GROUP:
#             svc.create_vfolder_in_group.return_value = created_vfolder_item
#     handler = VFolderHandler(vfolder_service=svc)
#     response = await handler.create_vfolder(mock_authenticated_request)
#     assert response.status == 200
#     assert response.text is not None
#     response_data = json.loads(response.text)
#     assert response_data == {"test": "response"}


# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "list_params,expected_count",
#     [
#         ({"all": True}, 1),
#         ({"all": False, "group_id": str(uuid.uuid4())}, 1),
#         ({"all": False, "owner_user_email": "test@test.com"}, 1),
#     ],
# )
# async def test_list_vfolders(
#     mock_vfolder_service,
#     mock_authenticated_request,
#     list_params: dict[str, Any],
#     expected_count: int,
# ):
#     mock_authenticated_request.query = list_params

#     user_identity = UserIdentity(
#             user_uuid=ctx.user_uuid,
#             user_role=ctx.user_role,
#             user_email=ctx.user_email,
#             domain_name=ctx.domain_name,
#         )
#     # mock service
#     svc = AsyncMock(VFolderServiceProtocol)
#     svc.get_vfolders.assert_called_once_with(user_identity, )
#     svc.get_vfolders.return_value = []

#     handler = VFolderHandler(vfolder_service=svc)
#     response = await handler.list_vfolders(mock_authenticated_request)
#     assert response.text is not None
#     response_data = json.loads(response.text)
#     assert len(response_data["root"]) == expected_count
#     if response_data["root"]:
#         assert response_data["root"][0]["user_email"] == "test@test.com"


# @pytest.mark.asyncio
# async def test_rename_vfolder_success(
#     mock_vfolder_service,
#     mock_authenticated_request,
# ):
#     mock_authenticated_request.can_read_body = True
#     mock_authenticated_request.json = AsyncMock(return_value={"new_name": "new-folder-name"})

#     handler = VFolderHandler(vfolder_service=mock_vfolder_service)
#     response = await handler.rename_vfolder(mock_authenticated_request)

#     assert response.status == 201


# @pytest.mark.asyncio
# async def test_delete_vfolder_success(
#     mock_vfolder_service,
#     mock_authenticated_request,
# ):
#     handler = VFolderHandler(vfolder_service=mock_vfolder_service)
#     response = await handler.delete_vfolder(mock_authenticated_request)

#     assert response.status == 204


# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "invalid_data",
#     [
#         {"name": ".bashrc", "folder_host": "test-host"},  # matches ^\.[a-z0-9]+rc$ pattern
#         {
#             "name": ".python_profile",
#             "folder_host": "test-host",
#         },  # matches ^\.[a-z0-9]+_profile$ pattern
#         {"name": "test" * 50, "folder_host": "test-host"},  # exceeds 64 char limit
#         {"name": "/etc", "folder_host": "test-host"},  # in RESERVED_VFOLDERS
#         {"name": "/tmp", "folder_host": "test-host"},
#     ],
# )
# async def test_create_vfolder_invalid_input(
#     mock_vfolder_service,
#     mock_authenticated_request,
#     invalid_data: dict[str, Any],
# ):
#     mock_authenticated_request.can_read_body = True
#     mock_authenticated_request.json = AsyncMock(return_value=invalid_data)

#     handler = VFolderHandler(vfolder_service=mock_vfolder_service)
#     with pytest.raises(InvalidAPIParameters):
#         await handler.create_vfolder(mock_authenticated_request)


# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "invalid_name",
#     [
#         ".bashrc",  # matches ^\.[a-z0-9]+rc$ pattern
#         ".bash_profile",  # matches ^\.[a-z0-9]+_profile$ pattern
#         ".python_profile",  # matches ^\.[a-z0-9]+_profile$ pattern
#         "test" * 50,  # exceeds 64 char limit
#         "/etc",  # in RESERVED_VFOLDERS
#     ],
# )
# async def test_rename_vfolder_invalid_name(
#     mock_vfolder_service,
#     mock_authenticated_request,
#     invalid_name: str,
# ):
#     mock_authenticated_request.can_read_body = True
#     mock_authenticated_request.json = AsyncMock(return_value={"new_name": invalid_name})

#     handler = VFolderHandler(vfolder_service=mock_vfolder_service)
#     with pytest.raises(InvalidAPIParameters):
#         await handler.rename_vfolder(mock_authenticated_request)
