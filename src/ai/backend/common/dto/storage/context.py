from typing import Self, override

from aiohttp import MultipartReader, web
from pydantic import ConfigDict, Field

from ai.backend.common.api_handlers import MiddlewareParam


class MultipartUploadCtx(MiddlewareParam):
    file_reader: MultipartReader = Field(
        ..., description="Multipart file reader for handling file uploads"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(file_reader=await request.multipart())
