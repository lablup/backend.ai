"""
Path parameter DTOs for image management REST API.
Manager-internal only (not shared with Client SDK).
"""

from __future__ import annotations

import uuid

from ai.backend.common.api_handlers import BaseRequestModel


class GetImagePathParam(BaseRequestModel):
    image_id: uuid.UUID
