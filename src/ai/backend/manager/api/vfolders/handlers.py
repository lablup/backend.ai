import uuid
from http import HTTPStatus
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
from ai.backend.common.dto.manager.response import VFolderCreateResponse, VFolderListResponse
from ai.backend.manager.data.vfolder.dto import (
    Keypair,
    UserIdentity,
    VFolderItem,
    VFolderItemToCreate,
)


class VFolderServiceProtocol(Protocol):
    async def create_vfolder_in_personal(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_info: VFolderItemToCreate,
    ) -> VFolderItem: ...

    async def create_vfolder_in_group(
        self,
        user_identity: UserIdentity,
        keypair: Keypair,
        vfolder_info: VFolderItemToCreate,
    ) -> VFolderItem: ...

    async def get_vfolders(
        self, user_identity: UserIdentity, group_id: Optional[uuid.UUID]
    ) -> list[VFolderItem]: ...

    async def rename_vfolder(
        self, user_identity: UserIdentity, keypair: Keypair, vfolder_id: uuid.UUID, new_name: str
    ) -> None: ...

    async def delete_vfolder(
        self,
        vfolder_id: uuid.UUID,
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
        vfolder_info = await VFolderItemToCreate.from_request(body.parsed)
        user_identity = UserIdentity.from_ctx(user_identity_ctx)
        keypair = Keypair.from_ctx(keypair_ctx)
        created_vfolder: VFolderItem
        if vfolder_info.group_id:
            created_vfolder = await self._vfolder_service.create_vfolder_in_group(
                user_identity=user_identity,
                keypair=keypair,
                vfolder_info=vfolder_info,
            )
        else:
            created_vfolder = await self._vfolder_service.create_vfolder_in_personal(
                user_identity=user_identity,
                keypair=keypair,
                vfolder_info=vfolder_info,
            )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=VFolderCreateResponse(item=created_vfolder.to_field()),
        )

    @api_handler
    async def list_vfolders(
        self, user_identity_ctx: UserIdentityCtx, query: QueryParam[ListGroupQuery]
    ) -> APIResponse:
        list_group_query = query.parsed
        user_identity = UserIdentity.from_ctx(user_identity_ctx)

        vfolder_list: list[VFolderItem] = await self._vfolder_service.get_vfolders(
            user_identity=user_identity, group_id=list_group_query.group_id
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=VFolderListResponse(
                items=[vfolder.to_field() for vfolder in vfolder_list]
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
        return APIResponse.no_content(status_code=HTTPStatus.CREATED)

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
            vfolder_id=parsed_path.vfolder_id,
        )
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)
