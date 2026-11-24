from __future__ import annotations

import asyncio
import ssl
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock

import aiohttp
import pytest
from aiotusclient.exceptions import TusUploadFailed
from yarl import URL

from ai.backend.client.exceptions import BackendConnectError
from ai.backend.client.func.vfolder import VFolderByName

_MAX_DOWNLOAD_RETRIES = 3


@dataclass(frozen=True)
class _FailingDownloadCase:
    id: str
    connection_error: aiohttp.ClientConnectorError
    expected_error: type[Exception]
    expected_attempts: int


@dataclass(frozen=True)
class _FailingDownload:
    storage_proxy_get: mock.MagicMock
    vfolder: VFolderByName
    file_path: Path


class TestVFolderDownload:
    @pytest.fixture
    def failing_download(
        self, case: _FailingDownloadCase, tmp_path: Path
    ) -> Iterator[_FailingDownload]:
        with mock.patch.object(
            aiohttp.ClientSession, "get", side_effect=case.connection_error
        ) as storage_proxy_get:
            yield _FailingDownload(
                storage_proxy_get=storage_proxy_get,
                vfolder=VFolderByName("myfolder"),
                file_path=tmp_path / "data.bin",
            )

    @pytest.mark.parametrize(
        "case",
        [
            _FailingDownloadCase(
                id="certificate-not-verified",
                connection_error=aiohttp.ClientConnectorCertificateError(
                    mock.MagicMock(host="storage.example", port=6022),
                    ssl.SSLCertVerificationError(1, "certificate verify failed"),
                ),
                expected_error=BackendConnectError,
                expected_attempts=1,
            ),
            _FailingDownloadCase(
                id="connection-refused",
                connection_error=aiohttp.ClientConnectorError(
                    mock.MagicMock(host="storage.example", port=6022),
                    ConnectionRefusedError(111, "Connection refused"),
                ),
                expected_error=RuntimeError,
                expected_attempts=_MAX_DOWNLOAD_RETRIES,
            ),
        ],
        ids=lambda case: case.id,
    )
    async def test_retries_only_errors_other_than_certificate_verification(
        self, case: _FailingDownloadCase, failing_download: _FailingDownload
    ) -> None:
        with pytest.raises(case.expected_error):
            await failing_download.vfolder._download_file(
                failing_download.file_path,
                URL("https://storage.example:6022/download"),
                chunk_size=1024,
                max_retries=_MAX_DOWNLOAD_RETRIES,
                show_progress=False,
            )

        assert failing_download.storage_proxy_get.call_count == case.expected_attempts


@dataclass(frozen=True)
class _FailingUploadCase:
    id: str
    connection_error: aiohttp.ClientConnectorError
    expected_error: type[Exception]


@dataclass(frozen=True)
class _FailingUpload:
    vfolder: VFolderByName
    file_path: Path


class TestVFolderUpload:
    @pytest.fixture
    def failing_upload(self, case: _FailingUploadCase, tmp_path: Path) -> Iterator[_FailingUpload]:
        file_path = tmp_path / "data.bin"
        file_path.write_bytes(b"hello")
        with (
            mock.patch("ai.backend.client.func.vfolder.Request") as request_class,
            mock.patch.object(aiohttp.ClientSession, "patch", side_effect=case.connection_error),
        ):
            upload_response = request_class.return_value.fetch.return_value.__aenter__.return_value
            upload_response.json = AsyncMock(
                return_value={"url": "https://storage.example:6022/upload", "token": "token"}
            )
            yield _FailingUpload(
                vfolder=VFolderByName("myfolder", id=uuid.uuid4()),
                file_path=file_path,
            )

    @pytest.mark.parametrize(
        "case",
        [
            _FailingUploadCase(
                id="certificate-not-verified",
                connection_error=aiohttp.ClientConnectorCertificateError(
                    mock.MagicMock(host="storage.example", port=6022),
                    ssl.SSLCertVerificationError(1, "certificate verify failed"),
                ),
                expected_error=BackendConnectError,
            ),
            _FailingUploadCase(
                id="connection-refused",
                connection_error=aiohttp.ClientConnectorError(
                    mock.MagicMock(host="storage.example", port=6022),
                    ConnectionRefusedError(111, "Connection refused"),
                ),
                expected_error=TusUploadFailed,
            ),
        ],
        ids=lambda case: case.id,
    )
    async def test_fails_without_waiting_for_a_retry(
        self, case: _FailingUploadCase, failing_upload: _FailingUpload
    ) -> None:
        with pytest.raises(case.expected_error):
            async with asyncio.timeout(5):
                await failing_upload.vfolder._upload_files(
                    [failing_upload.file_path], basedir=failing_upload.file_path.parent
                )
