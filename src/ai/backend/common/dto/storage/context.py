from typing import Optional, Self, override

from aiohttp import MultipartReader, web
from pydantic import ConfigDict, Field

from ai.backend.common.api_handlers import MiddlewareParam


class MultipartUploadCtx(MiddlewareParam):
    file_reader: MultipartReader = Field(
        ..., description="Multipart file reader for handling file uploads"
    )
    content_type: Optional[str] = Field(
        default=None, description="Content type from request headers"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        ctype_header = request.headers.get("Content-Type", "")
        if not ctype_header.startswith("multipart/form-data"):
            raise web.HTTPUnsupportedMediaType(reason="multipart/form-data required")

        # Extract content type from request headers if present
        content_type = request.headers.get("X-Content-Type")
        return cls(file_reader=await request.multipart(), content_type=content_type)
