import uuid
from typing import Any, Mapping, Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.common.api_handlers import MiddlewareParam
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.services.processors import Processors


class StorageSessionManagerCtx(MiddlewareParam):
    storage_manager: StorageSessionManager

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        return cls(storage_manager=root_ctx.storage_manager)


class ProcessorsCtx(MiddlewareParam):
    processors: Processors

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        return cls(processors=root_ctx.processors)


class RequestCtx(MiddlewareParam):
    request: web.Request

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(request=request)


class ValkeyArtifactCtx(MiddlewareParam):
    valkey_artifact: ValkeyArtifactDownloadTrackingClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        root_ctx: RootContext = request.app["_root.context"]
        return cls(valkey_artifact=root_ctx.valkey_artifact)


class UserContext(MiddlewareParam):
    """
    Middleware parameter providing authenticated user information.

    This context is populated by @auth_required decorator.
    """

    user_uuid: uuid.UUID
    user_email: str
    user_domain: str
    access_key: str

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(
            user_uuid=request["user"]["uuid"],
            user_email=request["user"]["email"],
            user_domain=request["user"]["domain_name"],
            access_key=request["keypair"]["access_key"],
        )


class VFolderAuthContext(MiddlewareParam):
    """
    Middleware parameter providing authenticated user and vfolder information.

    This context is populated by the following decorators:
    - @auth_required: Sets user authentication information
    - @with_vfolder_rows_resolved: Resolves vfolder and checks permissions
    - @with_vfolder_status_checked: Validates vfolder status
    """

    user_uuid: uuid.UUID
    user_email: str
    access_key: str
    vfolder_row: Mapping[str, Any]
    processors: Processors

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        # Get user info from auth middleware
        user_uuid = request["user"]["uuid"]
        user_email = request["user"]["email"]
        access_key = request["keypair"]["access_key"]

        # Get root context
        root_ctx: RootContext = request.app["_root.context"]

        # Get vfolder_row from decorator (set by @with_vfolder_rows_resolved and @with_vfolder_status_checked)
        row = request["vfolder_row"]

        return cls(
            user_uuid=user_uuid,
            user_email=user_email,
            access_key=access_key,
            vfolder_row=row,
            processors=root_ctx.processors,
        )
