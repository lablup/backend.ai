from __future__ import annotations

import uuid
from typing import Any, Protocol

import aiohttp

from ai.backend.common.cc_storage import (
    CONCURRENT_TIER,
    CipherPaths,
    FolderCipher,
    extension,
)
from ai.backend.manager.confidential.broker import BrokerClient
from ai.backend.manager.confidential.client_keys import (
    BrokerFolderKeyCustody,
    ClientKeyRelease,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class CatalogueView(Protocol):
    async def names(self) -> list[str]: ...

    async def read(self, name: str) -> bytes: ...


class _ProxyStore:
    def __init__(self, client: Any, volume: str, vfolder_id: str) -> None:
        self._client = client
        self._volume = volume
        self._vfolder_id = vfolder_id

    async def read(self, path: str) -> bytes:
        try:
            return await self._client.fetch_file_content(self._volume, self._vfolder_id, f"./{path}")
        except Exception as e:
            raise FileNotFoundError(path) from e

    async def write(self, path: str, data: bytes) -> None:
        raise PermissionError("the catalogue reader never writes")

    async def mkdir(self, path: str) -> None:
        raise PermissionError("the catalogue reader never writes")

    async def listdir(self, path: str) -> list[tuple[str, int, bool]]:
        result = await self._client.list_files(self._volume, self._vfolder_id, f"./{path or ''}")
        return [
            (item["name"], int(item.get("size") or 0), item.get("type") == "DIRECTORY")
            for item in result["items"]
        ]


class _PlainView:
    def __init__(self, store: _ProxyStore) -> None:
        self._store = store

    async def names(self) -> list[str]:
        return [name for name, _, is_dir in await self._store.listdir("") if not is_dir]

    async def read(self, name: str) -> bytes:
        return await self._store.read(name)


class _CipherView:
    def __init__(self, paths: CipherPaths, cipher: FolderCipher, store: _ProxyStore) -> None:
        self._paths = paths
        self._cipher = cipher
        self._store = store

    async def names(self) -> list[str]:
        return [entry.name for entry in await self._paths.listing("") if not entry.is_dir]

    async def read(self, name: str) -> bytes:
        return self._cipher.open(await self._store.read(await self._paths.resolve(name)))


class CatalogueReader:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def view(
        self,
        client: Any,
        volume: str,
        vfolder_id: str,
        *,
        domain_name: str,
        folder_uuid: uuid.UUID,
    ) -> CatalogueView:
        store = _ProxyStore(client, volume, vfolder_id)
        marker = extension().DIR_IV_FILE
        if all(name != marker for name, _, _ in await store.listdir("")):
            return _PlainView(store)
        async with aiohttp.ClientSession() as session:
            custody = BrokerFolderKeyCustody(BrokerClient(session))
            releases = ClientKeyRelease(self._db, custody)
            opts = await releases.opts_for_domain(domain_name)
            material = await custody.material(opts, domain_name, folder_uuid, CONCURRENT_TIER)
        cipher = FolderCipher(material)
        return _CipherView(cipher=cipher, paths=CipherPaths(cipher, store), store=store)
