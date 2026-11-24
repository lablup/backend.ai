from __future__ import annotations

import ssl
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from unittest import mock

import aiohttp
import pytest
from yarl import URL

from ai.backend.client.exceptions import BackendClientError
from ai.backend.client.func.vfolder import VFolderByName

_MAX_RETRIES = 3


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
                expected_error=BackendClientError,
                expected_attempts=1,
            ),
            _FailingDownloadCase(
                id="connection-refused",
                connection_error=aiohttp.ClientConnectorError(
                    mock.MagicMock(host="storage.example", port=6022),
                    ConnectionRefusedError(111, "Connection refused"),
                ),
                expected_error=RuntimeError,
                expected_attempts=_MAX_RETRIES,
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
                max_retries=_MAX_RETRIES,
                show_progress=False,
            )

        assert failing_download.storage_proxy_get.call_count == case.expected_attempts
