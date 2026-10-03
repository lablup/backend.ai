from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains_v2.vfolder import V2VFolderClient
from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CreateDownloadSessionPayload,
    CreateUploadSessionPayload,
)

from .conftest import MockAuth

_VFOLDER_ID = uuid4()
_STORAGE = "http://storage.example.com"


def _make_vfolder_client() -> V2VFolderClient:
    client = BackendAIAuthClient(
        ClientConfig(endpoint=URL("https://api.example.com")), MockAuth(), MagicMock()
    )
    return V2VFolderClient(client)


def _fake_http(resp: MagicMock) -> MagicMock:
    """aiohttp.ClientSession stand-in whose get() yields *resp*."""
    get_ctx = MagicMock()
    get_ctx.__aenter__ = AsyncMock(return_value=resp)
    get_ctx.__aexit__ = AsyncMock(return_value=False)
    http = MagicMock()
    http.get = MagicMock(return_value=get_ctx)
    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=http)
    session_ctx.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=session_ctx)


async def _chunks(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


class TestUploadFile:
    async def test_streams_the_file_to_the_session_url(self, tmp_path: Path) -> None:
        src = tmp_path / "train.jsonl"
        src.write_bytes(b"x" * 10)
        vf = _make_vfolder_client()
        create = AsyncMock(
            return_value=CreateUploadSessionPayload(token="tok", url=f"{_STORAGE}/upload")
        )
        uploader = MagicMock()
        uploader.upload = AsyncMock()
        tus_client = MagicMock()
        tus_client.async_uploader = MagicMock(return_value=uploader)

        with (
            patch.object(vf, "create_upload_session", create),
            patch("ai.backend.client.v2.domains_v2.vfolder.tus.TusClient", return_value=tus_client),
        ):
            await vf.upload_file(_VFOLDER_ID, src, chunk_size=4)

        request = create.call_args.args[1]
        assert (request.path, request.size) == ("train.jsonl", 10)
        kwargs = tus_client.async_uploader.call_args.kwargs
        assert kwargs["url"] == f"{_STORAGE}/upload?token=tok"
        assert kwargs["chunk_size"] == 4
        assert kwargs["file_stream"].closed
        uploader.upload.assert_awaited_once()

    async def test_dst_path_overrides_the_file_name(self, tmp_path: Path) -> None:
        src = tmp_path / "local.bin"
        src.write_bytes(b"")
        vf = _make_vfolder_client()
        create = AsyncMock(return_value=CreateUploadSessionPayload(token="t", url=_STORAGE))
        tus_client = MagicMock()
        tus_client.async_uploader.return_value.upload = AsyncMock()
        with (
            patch.object(vf, "create_upload_session", create),
            patch("ai.backend.client.v2.domains_v2.vfolder.tus.TusClient", return_value=tus_client),
        ):
            await vf.upload_file(_VFOLDER_ID, src, dst_path="data/remote.bin")

        assert create.call_args.args[1].path == "data/remote.bin"


class TestDownloadFile:
    async def test_writes_the_streamed_body(self, tmp_path: Path) -> None:
        dest = tmp_path / "out.bin"
        vf = _make_vfolder_client()
        create = AsyncMock(
            return_value=CreateDownloadSessionPayload(token="tok", url=f"{_STORAGE}/download")
        )
        resp = MagicMock(status=200)
        resp.content.iter_chunked = MagicMock(return_value=_chunks(b"ab", b"cd"))
        http_factory = _fake_http(resp)

        with (
            patch.object(vf, "create_download_session", create),
            patch("ai.backend.client.v2.domains_v2.vfolder.aiohttp.ClientSession", http_factory),
        ):
            await vf.download_file(_VFOLDER_ID, "dir/out.bin", dest, archive=True)

        assert dest.read_bytes() == b"abcd"
        request = create.call_args.args[1]
        assert (request.path, request.archive) == ("dir/out.bin", True)
        http = await http_factory.return_value.__aenter__()
        assert http.get.call_args.args[0] == URL(f"{_STORAGE}/download?token=tok")

    async def test_error_status_raises_and_writes_nothing(self, tmp_path: Path) -> None:
        dest = tmp_path / "missing.bin"
        vf = _make_vfolder_client()
        create = AsyncMock(return_value=CreateDownloadSessionPayload(token="t", url=_STORAGE))
        resp = MagicMock(status=404, reason="Not Found")
        resp.text = AsyncMock(return_value="no such file")

        with (
            patch.object(vf, "create_download_session", create),
            patch(
                "ai.backend.client.v2.domains_v2.vfolder.aiohttp.ClientSession", _fake_http(resp)
            ),
            pytest.raises(NotFoundError),
        ):
            await vf.download_file(_VFOLDER_ID, "missing.bin", dest)

        assert not dest.exists()
