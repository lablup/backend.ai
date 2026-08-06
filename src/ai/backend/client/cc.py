from __future__ import annotations

import io
from typing import Any

import aiohttp
from aiotusclient import client as tus
from yarl import URL

from ai.backend.common.cc_storage import (
    CipherPaths,
    FolderCipher,
    FolderKeyMaterial,
)

from .config import DEFAULT_CHUNK_SIZE
from .request import Request


class VFolderCipherStore:
    def __init__(self, folder: Any) -> None:
        self._folder = folder

    async def _session_url(self, verb: str, payload: dict[str, Any]) -> URL:
        rqst = Request("POST", f"/folders/{self._folder.request_key}/{verb}")
        rqst.set_json(payload)
        async with rqst.fetch() as resp:
            info = await resp.json()
        return URL(info["url"]).with_query({"token": info["token"]})

    async def read(self, path: str) -> bytes:
        url = await self._session_url("request-download", {"path": path})
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as resp:
                if resp.status == 404:
                    raise FileNotFoundError(path)
                resp.raise_for_status()
                return await resp.read()

    async def write(self, path: str, data: bytes) -> None:
        url = await self._session_url("request-upload", {"path": path, "size": len(data)})
        uploader = tus.TusClient().async_uploader(
            file_stream=io.BytesIO(data),
            url=url,
            upload_checksum=False,
            chunk_size=DEFAULT_CHUNK_SIZE,
        )
        await uploader.upload()

    async def mkdir(self, path: str) -> None:
        if not path:
            return
        rqst = Request("POST", f"/folders/{self._folder.request_key}/mkdir")
        rqst.set_json({"path": path, "parents": True, "exist_ok": True})
        async with rqst.fetch():
            pass

    async def listdir(self, path: str) -> list[tuple[str, int, bool]]:
        rqst = Request(
            "GET",
            f"/folders/{self._folder.request_key}/files",
            params={"path": path or "."},
        )
        async with rqst.fetch() as resp:
            items = (await resp.json())["items"]
        return [
            (item["name"], int(item.get("size") or 0), item.get("type") == "DIRECTORY")
            for item in items
        ]


async def acquire(folder: Any, session_id: str | None) -> tuple[CipherPaths, dict[str, Any]] | None:
    rqst = Request("POST", "/confidential/folder-keys")
    rqst.set_json({"vfolder_id": str(folder.id), "session_id": session_id})
    async with rqst.fetch() as resp:
        released = (await resp.json())["result"]
    if released.get("format") is None:
        return None
    cipher = FolderCipher(FolderKeyMaterial.from_json(released))
    return CipherPaths(cipher, VFolderCipherStore(folder)), released
