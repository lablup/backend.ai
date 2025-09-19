from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import override

from aiohttp import BodyPartReader, MultipartReader, web

from ai.backend.common.types import StreamReader
from ai.backend.logging import BraceStyleAdapter

_DEFAULT_UPLOAD_FILE_CHUNKS = 8192  # Default chunk size for streaming uploads

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class MultipartFileUploadStreamReader(StreamReader):
    _file_reader: MultipartReader

    def __init__(self, file_reader: MultipartReader) -> None:
        self._file_reader = file_reader

    @override
    async def read(self) -> AsyncIterator[bytes]:
        file_part = await self._file_reader.next()
        while file_part and not getattr(file_part, "filename", None):
            await file_part.release()
            file_part = await self._file_reader.next()

        # TODO: Make exception class
        if file_part is None:
            raise web.HTTPBadRequest(reason='No file part found (expected field "file")')
        if not isinstance(file_part, BodyPartReader):
            raise web.HTTPBadRequest(reason="Invalid file part")

        while True:
            chunk = await file_part.read_chunk(_DEFAULT_UPLOAD_FILE_CHUNKS)
            if not chunk:
                break
            yield chunk
