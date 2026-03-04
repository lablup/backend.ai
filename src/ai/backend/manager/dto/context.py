from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any, Self, override

from aiohttp import web
from pydantic import ConfigDict

from ai.backend.common.api_handlers import MiddlewareParam
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.processors import Processors


class RequestCtx(MiddlewareParam):
    request: web.Request

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(request=request)


class UserContext(MiddlewareParam):
    """
    Middleware parameter providing authenticated user information.

    This context is populated by @auth_required decorator.
    """

    user_uuid: uuid.UUID
    user_email: str
    user_domain: str
    user_role: UserRole
    access_key: str
    is_admin: bool
    is_superadmin: bool

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(
            user_uuid=request["user"]["uuid"],
            user_email=request["user"]["email"],
            user_domain=request["user"]["domain_name"],
            user_role=request["user"]["role"],
            access_key=request["keypair"]["access_key"],
            is_admin=request["is_admin"],
            is_superadmin=request["is_superadmin"],
        )


class ProcessorsCtx(MiddlewareParam):
    """Middleware parameter providing access to service processors."""

    processors: Processors

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(processors=request.app["_processors"])


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

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(
            user_uuid=request["user"]["uuid"],
            user_email=request["user"]["email"],
            access_key=request["keypair"]["access_key"],
            vfolder_row=request["vfolder_row"],
        )
