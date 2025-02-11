# import json
# import uuid
# from pathlib import Path
# from unittest.mock import AsyncMock

# import pytest
# from aiohttp import web

# from ai.backend.common.types import QuotaConfig, QuotaScopeID, QuotaScopeType, VFolderID
# from ai.backend.storage.api.vfolder.handler import VFolderHandler
# from ai.backend.storage.volumes.types import (
#     NewQuotaScopeCreated,
#     NewVFolderCreated,
#     QuotaScopeKeyData,
#     QuotaScopeMetadata,
#     VFolderKeyData,
#     VFolderMetadata,
#     VolumeKeyData,
#     VolumeMetadata,
#     VolumeMetadataList,
# )

# UUID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
# QUOTA_SCOPE_ID = QuotaScopeID(
#     scope_type=QuotaScopeType.USER,
#     scope_id=UUID,
# )
# VFOLDER_SCOPE_ID = VFolderID(
#     quota_scope_id=QUOTA_SCOPE_ID,
#     folder_id=UUID,
# )


# @pytest.fixture
# def mock_vfolder_service():
#     class MockVFolderService:
#         async def get_volume(self, volume_data: VolumeKeyData) -> VolumeMetadata:
#             return VolumeMetadata(
#                 volume_id=volume_data.volume_id,
#                 backend="mock-backend",
#                 path=Path("/mock/path"),
#                 fsprefix=None,
#                 capabilities=["read", "write"],
#             )

#         async def get_volumes(self) -> VolumeMetadataList:
#             return VolumeMetadataList(
#                 volumes=[
#                     VolumeMetadata(
#                         volume_id=UUID,
#                         backend="mock-backend",
#                         path=Path("/mock/path"),
#                         fsprefix=None,
#                         capabilities=["read", "write"],
#                     )
#                 ]
#             )

#         async def create_quota_scope(self, quota_data: QuotaScopeKeyData) -> NewQuotaScopeCreated:
#             return NewQuotaScopeCreated(
#                 quota_scope_id=QUOTA_SCOPE_ID,
#                 quota_scope_path=Path("/mock/quota/scope/path"),
#             )

#         async def get_quota_scope(self, quota_data: QuotaScopeKeyData) -> QuotaScopeMetadata:
#             return QuotaScopeMetadata(
#                 used_bytes=1024,
#                 limit_bytes=2048,
#             )

#         async def update_quota_scope(self, quota_data: QuotaScopeKeyData) -> None:
#             pass

#         async def delete_quota_scope(self, quota_data: QuotaScopeKeyData) -> None:
#             pass

#         async def create_vfolder(self, vfolder_data: VFolderKeyData) -> NewVFolderCreated:
#             return NewVFolderCreated(
#                 vfolder_id=VFOLDER_SCOPE_ID,
#                 quota_scope_path=Path("/mock/quota/scope/path"),
#                 vfolder_path=Path("/mock/vfolder/path"),
#             )

#         async def clone_vfolder(self, vfolder_data: VFolderKeyData) -> NewVFolderCreated:
#             return NewVFolderCreated(
#                 vfolder_id=VFOLDER_SCOPE_ID,
#                 quota_scope_path=Path("/mock/quota/scope/path"),
#                 vfolder_path=Path("/mock/vfolder/path"),
#             )

#         async def get_vfolder_info(self, vfolder_data: VFolderKeyData) -> VFolderMetadata:
#             return VFolderMetadata(
#                 mount_path=Path("/mock/mount/path"),
#                 file_count=100,
#                 capacity_bytes=1024 * 1024 * 1024,
#                 used_bytes=1024,
#                 fs_used_bytes=512000,
#             )

#         async def delete_vfolder(self, vfolder_data: VFolderKeyData) -> None:
#             pass

#     return MockVFolderService()


# @pytest.mark.asyncio
# async def test_get_volume(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {"volume_id": "123e4567-e89b-12d3-a456-426614174000"}
#         return request

#     response = await handler.get_volume(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_volume_id = json.loads(response.text)["volume_id"]
#     assert response_volume_id == "123e4567-e89b-12d3-a456-426614174000"


# @pytest.mark.asyncio
# async def test_get_volumes(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         return request

#     response = await handler.get_volumes(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_volumes = json.loads(response.text)["volumes"]
#     assert len(response_volumes) == 1


# @pytest.mark.asyncio
# async def test_create_quota_scope(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.json.return_value = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "quota_scope_id": QUOTA_SCOPE_ID,
#         }
#         return request

#     response = await handler.create_quota_scope(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 201


# @pytest.mark.asyncio
# async def test_get_quota_scope(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "quota_scope_id": QUOTA_SCOPE_ID,
#         }
#         return request

#     response = await handler.get_quota_scope(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_data = json.loads(response.text)["used_bytes"]
#     assert response_data == 1024


# @pytest.mark.asyncio
# async def test_update_quota_scope(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.json.return_value = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "quota_scope_id": QUOTA_SCOPE_ID,
#             "options": QuotaConfig(limit_bytes=2048),  # QuotaConfig 객체 사용
#         }
#         return request

#     response = await handler.update_quota_scope(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 204


# @pytest.mark.asyncio
# async def test_delete_quota_scope(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "quota_scope_id": QUOTA_SCOPE_ID,
#         }
#         return request

#     response = await handler.delete_quota_scope(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 204


# @pytest.mark.asyncio
# async def test_create_vfolder(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.json.return_value = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#         }
#         return request

#     response = await handler.create_vfolder(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 201


# @pytest.mark.asyncio
# async def test_clone_vfolder(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.json.return_value = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#             "dst_vfolder_id": VFOLDER_SCOPE_ID,
#         }
#         return request

#     response = await handler.clone_vfolder(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 201


# @pytest.mark.asyncio
# async def test_get_vfolder_info(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#             "subpath": "/mock/subpath",
#         }
#         return request

#     response = await handler.get_vfolder_info(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_data = json.loads(response.text)["mount_path"]
#     assert response_data == "/mock/mount/path"


# @pytest.mark.asyncio
# async def test_get_vfolder_mount(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#             "subpath": "/mock/subpath",
#         }
#         return request

#     response = await handler.get_vfolder_mount(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_data = json.loads(response.text)["mount_path"]
#     assert response_data == "/mock/mount/path"


# @pytest.mark.asyncio
# async def test_get_vfolder_usage(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#         }
#         return request

#     response = await handler.get_vfolder_usage(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_data = json.loads(response.text)["file_count"]
#     assert response_data == 100


# @pytest.mark.asyncio
# async def test_get_vfolder_used_bytes(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#         }
#         return request

#     response = await handler.get_vfolder_used_bytes(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_data = json.loads(response.text)["used_bytes"]
#     assert response_data == 1024


# @pytest.mark.asyncio
# async def test_get_vfolder_fs_usage(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#         }
#         return request

#     response = await handler.get_vfolder_fs_usage(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 200
#     assert response.content_type == "application/json"
#     response_data = json.loads(response.text)["capacity_bytes"]
#     assert response_data == 1024 * 1024 * 1024


# @pytest.mark.asyncio
# async def test_delete_vfolder(mock_vfolder_service):
#     handler = VFolderHandler(storage_service=mock_vfolder_service)

#     async def mock_request():
#         request = AsyncMock(spec=web.Request)
#         request.match_info = {
#             "volume_id": "123e4567-e89b-12d3-a456-426614174000",
#             "vfolder_id": VFOLDER_SCOPE_ID,
#         }
#         return request

#     response = await handler.delete_vfolder(await mock_request())

#     assert isinstance(response, web.Response)
#     assert response.status == 202
