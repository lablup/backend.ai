import uuid
from typing import (
    Protocol,
    Sequence,
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

    async def rename_vfodler(
        self, request: web.Request, params: VFolderRenameRequestModel
    ) -> CreatedResponseModel: ...

    async def delete_vfolder(
        self, request: web.Request, params: VFolderDeleteRequestModel
    ) -> NoContentResponseModel: ...


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
        self, user_identity: UserIdentity, vfolder_id: uuid.UUID, new_name: str
    ) -> None: ...

    async def delete_vfolder(
        self,
        vfolder_id: uuid.UUID,
        user_identity: UserIdentity,
        allowed_vfolder_types: Sequence[str],
        keypair: Keypair,
    ) -> None: ...
