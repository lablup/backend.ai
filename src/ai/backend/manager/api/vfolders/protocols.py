from typing import (
    Protocol,
)

from aiohttp import web

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


class VFolderHandlerProtocol(Protocol):
    async def create_vfolder(
        self, request: web.Request, params: VFolderCreateRequestModel
    ) -> VFolderCreateResponseModel: ...

    async def list_vfolders(
        self, request: web.Request, params: VFolderListRequestModel
    ) -> VFolderListResponseModel: ...

    async def rename_vfolder(
        self, request: web.Request, params: VFolderRenameRequestModel
    ) -> CreatedResponseModel: ...

    async def delete_vfolder(
        self, request: web.Request, params: VFolderDeleteRequestModel
    ) -> NoContentResponseModel: ...


class AuthenticatedHandlerProtocol(Protocol):
    def get_user_identity(self, request: web.Request) -> UserIdentity:
        return UserIdentity(
            user_uuid=request["user"]["uuid"],
            user_role=request["user"]["role"],
            user_email=request["user"]["email"],
            domain_name=request["user"]["domain_name"],
        )

    def get_keypair(self, request: web.Request) -> Keypair:
        return Keypair(
            access_key=request["keypair"]["access_key"],
            resource_policy=request["keypair"]["resource_policy"],
        )


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

    async def get_vfolders(self, user_identity: UserIdentity) -> VFolderList: ...

    async def rename_vfolder(
        self, user_identity: UserIdentity, keypair: Keypair, vfolder_id: str, new_name: str
    ) -> None: ...

    async def delete_vfolder(
        self,
        vfolder_id: str,
        user_identity: UserIdentity,
        keypair: Keypair,
    ) -> None: ...
