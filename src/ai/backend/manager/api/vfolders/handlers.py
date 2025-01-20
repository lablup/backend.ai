from aiohttp import web

from .protocols import VFolderServiceProtocol
from .types import (
    CreatedResponseModel,
    Keypair,
    NoContentResponseModel,
    UserIdentity,
    VFolderCreateRequestModel,
    VFolderCreateRequirements,
    VFolderCreateResponseModel,
    VFolderDeleteRequestModel,
    VFolderListRequestModel,
    VFolderListResponseModel,
    VFolderMetadata,
    VFolderRenameRequestModel,
)


class VFolderHandler:
    def __init__(self, vfolder_service: VFolderServiceProtocol):
        self.vfolder_service = vfolder_service

    async def create_vfolder(
        self, request: web.Request, params: VFolderCreateRequestModel
    ) -> VFolderCreateResponseModel:
        keypair: Keypair = Keypair(
            access_key=request["keypair"]["access_key"],
            resource_policy=request["keypair"]["resource_policy"],
        )

        user_identity: UserIdentity = UserIdentity(
            user_uuid=request["user"]["uuid"],
            user_role=request["user"]["role"],
            domain_name=request["user"]["domain_name"],
        )

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
        return VFolderListResponseModel()

    async def rename_vfodler(
        self, request: web.Request, params: VFolderRenameRequestModel
    ) -> CreatedResponseModel:
        return CreatedResponseModel()

    async def delete_vfolder(
        self, request: web.Request, params: VFolderDeleteRequestModel
    ) -> NoContentResponseModel:
        return NoContentResponseModel()
