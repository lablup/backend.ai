import uuid
from typing import Optional, Protocol

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
    api_handler,
)
from ai.backend.manager.api.vfolders.dtos import (
    Keypair,
    UserIdentity,
    VFolderCreateRequirements,
    VFolderList,
    VFolderMetadata,
)
from ai.backend.manager.api.vfolders.request import (
    DeleteVFolderId,
    KeypairModel,
    RenameVFolderId,
    UserIdentityModel,
    VFolderCreateData,
    VFolderListRequestedGroupId,
    VFolderNewName,
)
from ai.backend.manager.api.vfolders.response import VFolderCreateResponse, VFolderListResponse


class VFolderServiceProtocol(Protocol):
    async def create_vfolder_in_personal(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_create_requirements: VFolderCreateRequirements,
    ) -> VFolderMetadata: ...

    async def create_vfolder_in_group(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_create_requirements: VFolderCreateRequirements,
    ) -> VFolderMetadata: ...

    async def get_vfolders(
        self, user_identity: UserIdentity, group_id: Optional[uuid.UUID]
    ) -> VFolderList: ...

    async def rename_vfolder(
        self, user_identity: UserIdentity, keypair: Keypair, vfolder_id: uuid.UUID, new_name: str
    ) -> None: ...

    async def delete_vfolder(
        self,
        vfolder_id: str,
        user_identity: UserIdentity,
        keypair: Keypair,
    ) -> None: ...


class VFolderHandler:
    def __init__(self, vfolder_service: VFolderServiceProtocol):
        self.vfolder_service = vfolder_service

    @api_handler
    async def create_vfolder(
        self,
        keypair: KeypairModel,
        user_identity: UserIdentityModel,
        body: BodyParam[VFolderCreateData],
    ) -> APIResponse:
        parsed_body = body.parsed
        create_requirements: VFolderCreateRequirements = parsed_body.to_dto()

        vfolder_metadata: VFolderMetadata
        if create_requirements.group_id:
            vfolder_metadata = await self.vfolder_service.create_vfolder_in_group(
                user_identity=user_identity.to_dto(),
                keypair=keypair.to_dto(),
                vfolder_create_requirements=create_requirements,
            )
        else:
            vfolder_metadata = await self.vfolder_service.create_vfolder_in_personal(
                user_identity=user_identity.to_dto(),
                keypair=keypair.to_dto(),
                vfolder_create_requirements=create_requirements,
            )

        return APIResponse.build(
            status_code=200,
            response_model=VFolderCreateResponse.from_vfolder_metadata(vfolder_metadata),
        )

    @api_handler
    async def list_vfolders(
        self, user_identity: UserIdentityModel, query: QueryParam[VFolderListRequestedGroupId]
    ) -> APIResponse:
        parsed_query = query.parsed

        vfolder_list: VFolderList = await self.vfolder_service.get_vfolders(
            user_identity=user_identity.to_dto(), group_id=parsed_query.group_id
        )

        return APIResponse.build(
            status_code=200,
            response_model=VFolderListResponse.from_dataclass(vfolder_list=vfolder_list),
        )

    @api_handler
    async def rename_vfolder(
        self,
        keypair: KeypairModel,
        user_identity: UserIdentityModel,
        path: PathParam[RenameVFolderId],
        body: BodyParam[VFolderNewName],
    ) -> APIResponse:
        parsed_path = path.parsed
        parsed_body = body.parsed

        vfolder_id: uuid.UUID = parsed_path.vfolder_id
        new_name: str = parsed_body.new_name

        await self.vfolder_service.rename_vfolder(
            user_identity=user_identity.to_dto(),
            keypair=keypair.to_dto(),
            vfolder_id=vfolder_id,
            new_name=new_name,
        )

        return APIResponse.no_content(status_code=201)

    @api_handler
    async def delete_vfolder(
        self,
        keypair: KeypairModel,
        user_identity: UserIdentityModel,
        path: PathParam[DeleteVFolderId],
    ) -> APIResponse:
        parsed_path = path.parsed

        await self.vfolder_service.delete_vfolder(
            user_identity=user_identity.to_dto(),
            keypair=keypair.to_dto(),
            vfolder_id=str(parsed_path.vfolder_id),
        )

        return APIResponse.no_content(status_code=204)
