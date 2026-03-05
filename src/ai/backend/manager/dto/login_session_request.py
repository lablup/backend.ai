"""
Manager-specific path parameter models for login session REST API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class RevokeLoginSessionPathParam(BaseRequestModel):
    session_id: str = Field(description="The login session ID to revoke")
