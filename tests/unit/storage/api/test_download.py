from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import jwt
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient

from ai.backend.storage.api.client import download

_SECRET = "test-secret-for-download-handler-tests"
_CONTENT = b"0123456789"


def _http_date(dt: datetime) -> str:
    return format_datetime(dt, usegmt=True)


@pytest.fixture
def vfolder(tmp_path: Path) -> Path:
    path = tmp_path / "vfolder"
    path.mkdir()
    return path


@pytest.fixture
def outside(tmp_path: Path) -> Path:
    path = tmp_path / "outside"
    path.mkdir()
    (path / "secret.txt").write_bytes(b"outside")
    return path


@pytest.fixture
def data_file(vfolder: Path) -> Path:
    path = vfolder / "data.bin"
    path.write_bytes(_CONTENT)
    return path


@pytest.fixture
def make_token() -> Callable[[str], str]:
    def _make(relpath: str) -> str:
        return jwt.encode(
            {
                "op": "download",
                "volume": "test-volume",
                "vfid": str(uuid.uuid4()),
                "relpath": relpath,
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            _SECRET,
            algorithm="HS256",
        )

    return _make


@pytest.fixture
async def client(vfolder: Path, aiohttp_client: Any) -> TestClient[Any, Any]:
    volume = MagicMock()
    volume.mangle_vfpath.return_value = vfolder
    ctx = MagicMock()
    ctx.local_config.storage_proxy.secret = _SECRET
    ctx.volume_pool.get_volume_by_name.return_value = volume
    app = web.Application()
    app["ctx"] = ctx
    app.router.add_get("/download", download)
    return await aiohttp_client(app)


@pytest.fixture
def data_file_etag(data_file: Path) -> str:
    st = data_file.stat()
    return f'"{st.st_mtime_ns:x}-{st.st_size:x}"'


class TestDownloadRange:
    @pytest.mark.usefixtures("data_file")
    async def test_full_download(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get("/download", params={"token": make_token("data.bin")})

        assert resp.status == 200
        assert await resp.read() == _CONTENT
        assert resp.headers["Content-Length"] == str(len(_CONTENT))
        assert resp.headers["Accept-Ranges"] == "bytes"
        assert "filename*=UTF-8''data.bin" in resp.headers["Content-Disposition"]

    @pytest.mark.parametrize(
        ("range_header", "content_range", "body"),
        [
            ("bytes=0-1", "bytes 0-1/10", b"01"),
            ("bytes=4-", "bytes 4-9/10", b"456789"),
            ("bytes=-3", "bytes 7-9/10", b"789"),
            ("bytes=8-100", "bytes 8-9/10", b"89"),
        ],
    )
    @pytest.mark.usefixtures("data_file")
    async def test_partial_download(
        self,
        client: TestClient[Any, Any],
        make_token: Callable[[str], str],
        range_header: str,
        content_range: str,
        body: bytes,
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={"Range": range_header},
        )

        assert resp.status == 206
        assert resp.headers["Content-Range"] == content_range
        assert await resp.read() == body

    @pytest.mark.parametrize("range_header", ["bytes=10-", "bytes=20-30", "lines=0-1"])
    @pytest.mark.usefixtures("data_file")
    async def test_unsatisfiable_range(
        self,
        client: TestClient[Any, Any],
        make_token: Callable[[str], str],
        range_header: str,
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={"Range": range_header},
        )

        assert resp.status == 416
        assert resp.headers["Content-Range"] == "bytes */10"

    @pytest.mark.usefixtures("data_file")
    async def test_stale_if_range_returns_full_body(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={
                "Range": "bytes=0-1",
                "If-Range": _http_date(datetime.now(UTC) - timedelta(days=1)),
            },
        )

        assert resp.status == 200
        assert await resp.read() == _CONTENT


class TestDownloadPreconditions:
    async def test_matching_if_none_match_returns_not_modified(
        self,
        client: TestClient[Any, Any],
        make_token: Callable[[str], str],
        data_file_etag: str,
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={"If-None-Match": data_file_etag},
        )

        assert resp.status == 304
        assert resp.headers["ETag"] == data_file_etag
        assert await resp.read() == b""

    @pytest.mark.usefixtures("data_file")
    async def test_other_if_none_match_returns_full_body(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={"If-None-Match": '"other"'},
        )

        assert resp.status == 200
        assert await resp.read() == _CONTENT

    @pytest.mark.usefixtures("data_file")
    async def test_unchanged_if_modified_since_returns_not_modified(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={"If-Modified-Since": _http_date(datetime.now(UTC) + timedelta(days=1))},
        )

        assert resp.status == 304

    @pytest.mark.usefixtures("data_file")
    async def test_other_if_match_fails_precondition(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={"If-Match": '"other"'},
        )

        assert resp.status == 412

    async def test_matching_if_match_returns_full_body(
        self,
        client: TestClient[Any, Any],
        make_token: Callable[[str], str],
        data_file_etag: str,
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={"If-Match": data_file_etag},
        )

        assert resp.status == 200
        assert await resp.read() == _CONTENT

    @pytest.mark.usefixtures("data_file")
    async def test_modified_after_if_unmodified_since_fails_precondition(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get(
            "/download",
            params={"token": make_token("data.bin")},
            headers={
                "If-Unmodified-Since": _http_date(datetime.now(UTC) - timedelta(days=1)),
            },
        )

        assert resp.status == 412


class TestDownloadPathSafety:
    @pytest.fixture
    def symlinked_file(self, vfolder: Path, outside: Path) -> Path:
        link = vfolder / "link.txt"
        link.symlink_to(outside / "secret.txt")
        return link

    @pytest.fixture
    def symlinked_dir(self, vfolder: Path, outside: Path) -> Path:
        link = vfolder / "sub"
        link.symlink_to(outside)
        return link

    @pytest.fixture
    def inner_symlink(self, vfolder: Path, data_file: Path) -> Path:
        link = vfolder / "alias.bin"
        link.symlink_to(data_file)
        return link

    @pytest.fixture
    def inner_dir(self, vfolder: Path) -> Path:
        path = vfolder / "dir"
        path.mkdir()
        return path

    @pytest.mark.usefixtures("symlinked_file")
    async def test_symlink_to_outside_file_is_not_found(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get("/download", params={"token": make_token("link.txt")})

        assert resp.status == 404

    @pytest.mark.usefixtures("symlinked_dir")
    async def test_symlinked_directory_to_outside_is_not_found(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get("/download", params={"token": make_token("sub/secret.txt")})

        assert resp.status == 404

    @pytest.mark.usefixtures("outside")
    async def test_escaping_path_is_not_found(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get("/download", params={"token": make_token("../outside/secret.txt")})

        assert resp.status == 404

    async def test_missing_file_is_not_found(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get("/download", params={"token": make_token("missing.bin")})

        assert resp.status == 404

    @pytest.mark.usefixtures("inner_symlink")
    async def test_symlink_inside_vfolder_is_followed(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get("/download", params={"token": make_token("alias.bin")})

        assert resp.status == 200
        assert await resp.read() == _CONTENT
        assert "filename*=UTF-8''alias.bin" in resp.headers["Content-Disposition"]

    @pytest.mark.usefixtures("inner_dir")
    async def test_directory_without_archive_is_rejected(
        self, client: TestClient[Any, Any], make_token: Callable[[str], str]
    ) -> None:
        resp = await client.get("/download", params={"token": make_token("dir")})

        assert resp.status == 400
