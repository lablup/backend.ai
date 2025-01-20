from pathlib import Path
from typing import List, Protocol

import aiohttp_cors
from aiohttp import web
from pydantic import BaseModel

from ai.backend.common.types import VFolderID


class DownloadTokenData(BaseModel):
    volume: str
    vfid: VFolderID
    relpath: str
    archive: bool
    unmanaged_path: str | None


class UploadTokenData(BaseModel):
    volume: str
    vfid: VFolderID
    relpath: str
    session: str
    size: int


class AbstractVolumeClient(Protocol):
    async def download(self, token: DownloadTokenData) -> Path:
        ...

    async def upload(self, token: UploadTokenData) -> None:
        ...

    async def get_volumes(self) -> List[str]:
        ...


class VolumeClient(AbstractVolumeClient):
    async def download(self, token: DownloadTokenData) -> Path:
        ...

    async def upload(self, token: UploadTokenData) -> None:
        ...

    async def get_volumes(self) -> List[str]:
        ...


class VolumeClientHandler(AbstractVolumeClient):
    def __init__(self, volume_client: AbstractVolumeClient):
        self.volume_client = volume_client


async def init_client_app() -> web.Application:
    app = web.Application()
    cors = aiohttp_cors.setup(app)

    return app
