import uuid
from typing import Optional, Protocol

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.dto.manager.context import KeypairCtx, UserIdentityCtx
from ai.backend.common.dto.manager.path import VFolderIDPath
from ai.backend.common.dto.manager.query import ListGroupQuery
from ai.backend.common.dto.manager.request import (
    RenameVFolderReq,
    VFolderCreateReq,
)
from ai.backend.common.dto.manager.response import VFolderListResponse
from ai.backend.manager.data.vfolder.dto import (
    Keypair,
    UserIdentity,
    VFolderInfo,
    VFolderItemToCreate,
    VFolderListItem,
)


class VFolderServiceProtocol(Protocol):
    async def create_vfolder_in_personal(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_item: VFolderItemToCreate,
    ) -> VFolderInfo: ...

    async def create_vfolder_in_group(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_item: VFolderItemToCreate,
    ) -> VFolderInfo: ...

    async def get_vfolders(
        self, user_identity: UserIdentity, group_id: Optional[uuid.UUID]
    ) -> list[VFolderListItem]: ...

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
    _vfolder_service: VFolderServiceProtocol

    def __init__(self, vfolder_service: VFolderServiceProtocol):
        self._vfolder_service = vfolder_service

    @api_handler
    async def create_vfolder(
        self,
        keypair_ctx: KeypairCtx,
        user_identity_ctx: UserIdentityCtx,
        body: BodyParam[VFolderCreateReq],
    ) -> APIResponse:
        vfolder_item = VFolderItemToCreate.from_request(body.parsed)
        user_identity = UserIdentity.from_ctx(user_identity_ctx)
        keypair = Keypair.from_ctx(keypair_ctx)
        created_vfolder_info: VFolderInfo
        if vfolder_item.group_id:
            created_vfolder_info = await self._vfolder_service.create_vfolder_in_group(
                user_identity=user_identity,
                keypair=keypair,
                vfolder_item=vfolder_item,
            )
        else:
            created_vfolder_info = await self._vfolder_service.create_vfolder_in_personal(
                user_identity=user_identity,
                keypair=keypair,
                vfolder_item=vfolder_item,
            )

        return APIResponse.build(
            status_code=200,
            response_model=created_vfolder_info.to_vfolder_create_response(),
        )

    @api_handler
    async def list_vfolders(
        self, user_identity_ctx: UserIdentityCtx, query: QueryParam[ListGroupQuery]
    ) -> APIResponse:
        list_group_query = query.parsed
        user_identity = UserIdentity.from_ctx(user_identity_ctx)

        vfolder_list = await self._vfolder_service.get_vfolders(
            user_identity=user_identity, group_id=list_group_query.group_id
        )

        return APIResponse.build(
            status_code=200,
            response_model=VFolderListResponse(
                items=[vfolder.to_response() for vfolder in vfolder_list]
            ),
        )

    @api_handler
    async def rename_vfolder(
        self,
        keypair_ctx: KeypairCtx,
        user_identity_ctx: UserIdentityCtx,
        path: PathParam[VFolderIDPath],
        body: BodyParam[RenameVFolderReq],
    ) -> APIResponse:
        vfolder_id: uuid.UUID = path.parsed.vfolder_id
        new_name: str = body.parsed.new_name
        user_identity = UserIdentity.from_ctx(user_identity_ctx)
        keypair = Keypair.from_ctx(keypair_ctx)

        await self._vfolder_service.rename_vfolder(
            user_identity=user_identity,
            keypair=keypair,
            vfolder_id=vfolder_id,
            new_name=new_name,
        )
        return APIResponse.no_content(status_code=201)

    @api_handler
    async def delete_vfolder(
        self,
        keypair_ctx: KeypairCtx,
        user_identity_ctx: UserIdentityCtx,
        path: PathParam[VFolderIDPath],
    ) -> APIResponse:
        parsed_path = path.parsed
        user_identity = UserIdentity.from_ctx(user_identity_ctx)
        keypair = Keypair.from_ctx(keypair_ctx)

        await self._vfolder_service.delete_vfolder(
            user_identity=user_identity,
            keypair=keypair,
            vfolder_id=str(parsed_path.vfolder_id),
        )
        return APIResponse.no_content(status_code=204)
