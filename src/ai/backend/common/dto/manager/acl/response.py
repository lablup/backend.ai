from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("GetPermissionsResponse",)


class GetPermissionsResponse(BaseResponseModel):
    vfolder_host_permission_list: list[str] = Field(
        description="List of all available vfolder host permissions",
    )
