from aiohttp import web

from .protocols import AuthenticatedHandlerProtocol, VFolderHandlerProtocol, VFolderServiceProtocol
from .types import (
    CreatedResponseModel,
    Keypair,
    NoContentResponseModel,
    UserIdentity,
    VFolderCreateRequestModel,
    VFolderCreateRequirements,
    VFolderCreateResponseModel,
    VFolderDeleteRequestModel,
    VFolderList,
    VFolderListRequestModel,
    VFolderListResponseModel,
    VFolderMetadata,
    VFolderRenameRequestModel,
)


class VFolderHandler(VFolderHandlerProtocol, AuthenticatedHandlerProtocol):
    def __init__(self, vfolder_service: VFolderServiceProtocol):
        self.vfolder_service = vfolder_service

    async def create_vfolder(
        self, request: web.Request, params: VFolderCreateRequestModel
    ) -> VFolderCreateResponseModel:
        keypair: Keypair = self.get_keypair(request=request)
        user_identity: UserIdentity = self.get_user_identity(request=request)
        create_requirements: VFolderCreateRequirements = VFolderCreateRequirements.from_params(
            params=params
        )

        vfolder_metadata: VFolderMetadata
        if create_requirements.group:
            vfolder_metadata = await self.vfolder_service.create_vfolder_in_group(
                user_identity=user_identity,
                keypair=keypair,
                vfolder_create_requirements=create_requirements,
            )
        else:
            vfolder_metadata = await self.vfolder_service.create_vfolder_in_personal(
                user_identity=user_identity,
                keypair=keypair,
                vfolder_create_requirements=create_requirements,
            )

        return VFolderCreateResponseModel.from_vfolder_metadata(vfolder_metadata)

    async def list_vfolders(
        self, request: web.Request, params: VFolderListRequestModel
    ) -> VFolderListResponseModel:
        user_identity: UserIdentity = self.get_user_identity(request=request)
        vfolder_list: VFolderList = await self.vfolder_service.get_vfolders(
            user_identity=user_identity
        )

        return VFolderListResponseModel.from_dataclass(vfolder_list=vfolder_list)

    async def rename_vfolder(
        self, request: web.Request, params: VFolderRenameRequestModel
    ) -> CreatedResponseModel:
        vfolder_id: str = request.match_info["vfolder_id"]
        keypair: Keypair = self.get_keypair(request=request)
        user_identity: UserIdentity = self.get_user_identity(request=request)

        await self.vfolder_service.rename_vfolder(
            user_identity=user_identity,
            keypair=keypair,
            vfolder_id=vfolder_id,
            new_name=params.new_name,
        )

        return CreatedResponseModel()

    async def delete_vfolder(
        self, request: web.Request, params: VFolderDeleteRequestModel
    ) -> NoContentResponseModel:
        keypair: Keypair = self.get_keypair(request=request)
        user_identity: UserIdentity = self.get_user_identity(request=request)

        await self.vfolder_service.delete_vfolder(
            user_identity=user_identity, keypair=keypair, vfolder_id=str(params.vfolder_id)
        )

        return NoContentResponseModel()
