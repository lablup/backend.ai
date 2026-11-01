"""
Tests for TUS upload offset validation in tus_upload_part().
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_tus import (
    TusSessionId,
    TusSessionNotFoundError,
)
from ai.backend.common.types import VFolderID
from ai.backend.storage.api.client import (
    _commit_upload,
    _drain_into_upload_file,
    tus_upload_part,
)
from ai.backend.storage.api.manager import create_upload_session
from ai.backend.storage.errors import (
    InvalidAPIParameters,
    InvalidSubpathError,
    UploadOffsetMismatchError,
)


class TestTusUploadPartOffsetValidation:
    """Tests for Upload-Offset header validation in tus_upload_part()."""

    # =========================================================================
    # Low-level fixtures (internal building blocks)
    # =========================================================================

    @pytest.fixture
    def token_data(self) -> dict[str, Any]:
        """Create mock token data."""
        return {
            "volume": "test-volume",
            "vfid": MagicMock(),
            "session": "test-session",
            "size": "10240",
            "relpath": "test-file.txt",
        }

    @pytest.fixture(autouse=True)
    def _patch_disk_helpers(self) -> Generator[None, None, None]:
        """Mock the aiofiles-based file write path with no-ops.

        ``tus_upload_part`` opens the upload file via ``aiofiles.open`` and
        streams the request body straight in under the lease. None of these
        paths exist on disk in mocked tests, so we substitute an AsyncMock
        for both the file handle and the wrapped ``fsync``. The offset
        validation logic (which is what these tests cover) executes before
        the file open, so this leaves the assertions intact.
        """
        async_file = AsyncMock()
        async_file.fileno = MagicMock(return_value=99)
        file_cm = MagicMock()
        file_cm.__aenter__ = AsyncMock(return_value=async_file)
        file_cm.__aexit__ = AsyncMock(return_value=None)
        with (
            patch("ai.backend.storage.api.client.aiofiles.open", return_value=file_cm),
            patch("ai.backend.storage.api.client.os.fsync"),
        ):
            yield

    def _create_mock_request(
        self,
        tmp_path: Path,
        client_offset: str | None,
        *,
        server_offset: int | None = 1024,
    ) -> MagicMock:
        """Create a fully configured mock request."""
        # Mock volume
        volume = MagicMock()
        volume.mangle_vfpath.return_value = tmp_path

        # Mock Valkey TUS coordinator (try_load_offset / advance_offset).
        valkey_tus_client = AsyncMock()
        valkey_tus_client.get_offset = AsyncMock(return_value=server_offset)
        valkey_tus_client.try_load_offset = AsyncMock(return_value=server_offset or 0)
        valkey_tus_client.advance_offset = AsyncMock(return_value=server_offset or 0)
        valkey_tus_client.extend_lease = AsyncMock(return_value=None)
        valkey_tus_client.release_lease = AsyncMock(return_value=None)

        # Mock context
        ctx = MagicMock()
        ctx.local_config.storage_proxy.secret = "test-secret"
        ctx.node_id = "test-node"
        ctx.valkey_tus_client = valkey_tus_client
        ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
        ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock request
        request = MagicMock(spec=web.Request)
        request.app = {"ctx": ctx}
        request.headers = {}
        request.query = {"token": "test-token"}

        if client_offset is not None:
            request.headers["Upload-Offset"] = client_offset

        # Mock content reader (returns EOF immediately)
        content = AsyncMock()
        content.at_eof.return_value = True
        request.content = content

        return request

    # =========================================================================
    # Scenario fixtures (composed, one per test scenario)
    # =========================================================================

    @pytest.fixture
    def request_without_offset_header(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Missing Upload-Offset header."""
        request = self._create_mock_request(tmp_path, client_offset=None)

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_with_invalid_offset(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Invalid (non-integer) Upload-Offset header."""
        request = self._create_mock_request(tmp_path, client_offset="not-a-number")

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_offset_mismatch_client_behind(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Client offset (512) behind server offset (1024)."""
        request = self._create_mock_request(tmp_path, client_offset="512", server_offset=1024)

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_offset_mismatch_client_ahead(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Client offset (2048) ahead of server offset (1024)."""
        request = self._create_mock_request(tmp_path, client_offset="2048", server_offset=1024)

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_with_matching_offset(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Client offset matches server offset (both 1024)."""
        request = self._create_mock_request(tmp_path, client_offset="1024", server_offset=1024)

        # Create upload temp file (for downstream finalization paths)
        upload_parent = tmp_path / ".upload"
        upload_parent.mkdir(parents=True, exist_ok=True)
        temp_file = upload_parent / token_data["session"]
        temp_file.write_bytes(b"x" * 1024)

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_with_zero_offset(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: New file upload with zero offset."""
        request = self._create_mock_request(tmp_path, client_offset="0", server_offset=0)

        # Create empty upload temp file
        upload_parent = tmp_path / ".upload"
        upload_parent.mkdir(parents=True, exist_ok=True)
        temp_file = upload_parent / token_data["session"]
        temp_file.write_bytes(b"")

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "0"}

            yield request

    # =========================================================================
    # Test methods (minimal fixture injection, Act & Assert only)
    # =========================================================================

    async def test_missing_upload_offset_header_raises_bad_request(
        self,
        request_without_offset_header: MagicMock,
    ) -> None:
        """When Upload-Offset header is missing, should raise InvalidAPIParameters (400)."""
        with pytest.raises(InvalidAPIParameters):
            await tus_upload_part(request_without_offset_header)

    async def test_invalid_upload_offset_header_raises_bad_request(
        self,
        request_with_invalid_offset: MagicMock,
    ) -> None:
        """When Upload-Offset header is not a valid integer, should raise InvalidAPIParameters (400)."""
        with pytest.raises(InvalidAPIParameters):
            await tus_upload_part(request_with_invalid_offset)

    async def test_offset_mismatch_client_behind_raises_conflict(
        self,
        request_offset_mismatch_client_behind: MagicMock,
    ) -> None:
        """When client offset is behind server file size, should raise UploadOffsetMismatchError (409)."""
        with pytest.raises(UploadOffsetMismatchError):
            await tus_upload_part(request_offset_mismatch_client_behind)

    async def test_offset_mismatch_client_ahead_raises_conflict(
        self,
        request_offset_mismatch_client_ahead: MagicMock,
    ) -> None:
        """When client offset is ahead of server file size, should raise UploadOffsetMismatchError (409)."""
        with pytest.raises(UploadOffsetMismatchError):
            await tus_upload_part(request_offset_mismatch_client_ahead)

    async def test_matching_offset_proceeds_with_upload(
        self,
        request_with_matching_offset: MagicMock,
    ) -> None:
        """When client offset matches server file size, upload should proceed successfully."""
        # No exception should be raised
        await tus_upload_part(request_with_matching_offset)

    async def test_new_file_upload_with_zero_offset(
        self,
        request_with_zero_offset: MagicMock,
    ) -> None:
        """When both client offset and file size are 0, upload should proceed successfully."""
        # No exception should be raised
        await tus_upload_part(request_with_zero_offset)


class TestDrainOrphanBytesRecovery:
    """Idempotent recovery when a prior PATCH wrote bytes to disk but did not
    update the Valkey offset (e.g. ``advance_offset`` raised
    ``TusLeaseLostError`` after a successful drain, or the storage-proxy
    crashed between ``fsync`` and the ``INCRBY`` Lua step).

    The next PATCH must:
      1. ``truncate`` the staging file back to the Valkey-canonical offset
         so the orphan tail bytes are discarded.
      2. Append the client-replayed chunk from there.

    The on-disk content after the retry must be identical to what it would
    have been if the prior PATCH had never landed on disk.
    """

    async def test_orphan_tail_is_truncated_then_overwritten(
        self,
        tmp_path: Path,
    ) -> None:
        committed_offset = 1024
        committed_payload = b"\x11" * committed_offset
        orphan_tail = b"\x22" * 512
        retry_payload = b"\x33" * 768

        upload_temp_path = tmp_path / "session-id"
        # State left by the prior PATCH: committed bytes + orphan tail.
        upload_temp_path.write_bytes(committed_payload + orphan_tail)

        # Client-replayed chunk feed. ``at_eof`` is sync on aiohttp.StreamReader;
        # ``read`` is async — model each accordingly so the drain loop iterates.
        content = AsyncMock()
        content.at_eof = MagicMock(side_effect=[False, True])
        content.read = AsyncMock(side_effect=[retry_payload])

        bytes_written = await _drain_into_upload_file(
            content,
            upload_temp_path,
            start_offset=committed_offset,
            session_id=TusSessionId("test-session"),
        )

        assert bytes_written == len(retry_payload)
        final_bytes = upload_temp_path.read_bytes()
        assert final_bytes == committed_payload + retry_payload
        # The orphan tail bytes are gone; the prior failure did not corrupt
        # the file as observed by future PATCHes.
        assert orphan_tail not in final_bytes[committed_offset:]


_SESSION = "test-session"
_PAYLOAD = b"payload"


@pytest.fixture
def vfolder(tmp_path: Path) -> Path:
    path = tmp_path / "vfolder"
    path.mkdir()
    return path


@pytest.fixture
def outside(tmp_path: Path) -> Path:
    path = tmp_path / "outside"
    path.mkdir()
    return path


@pytest.fixture
def staging_file(vfolder: Path) -> Path:
    upload_dir = vfolder / ".upload"
    upload_dir.mkdir()
    path = upload_dir / _SESSION
    path.write_bytes(_PAYLOAD)
    return path


def _body() -> AsyncMock:
    content = AsyncMock()
    content.at_eof = MagicMock(side_effect=[False, True])
    content.read = AsyncMock(side_effect=[_PAYLOAD])
    return content


def _upload_request(
    vfolder: Path,
    *,
    relpath: str,
    dst_dir: str | None = None,
    upload_offset: int = 0,
    size: int = len(_PAYLOAD),
) -> tuple[MagicMock, Any]:
    """Build a PATCH request and the ``check_params`` patcher carrying its token."""
    volume = MagicMock()
    volume.mangle_vfpath.return_value = vfolder
    valkey_tus_client = AsyncMock()
    valkey_tus_client.try_load_offset = AsyncMock(return_value=upload_offset)
    valkey_tus_client.advance_offset = AsyncMock(return_value=upload_offset + len(_PAYLOAD))
    ctx = MagicMock()
    ctx.node_id = "test-node"
    ctx.valkey_tus_client = valkey_tus_client
    ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
    ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)
    request = MagicMock(spec=web.Request)
    request.app = {"ctx": ctx}
    request.headers = {"Upload-Offset": str(upload_offset)}
    request.content = _body()
    token = {
        "volume": "test-volume",
        "vfid": MagicMock(),
        "session": _SESSION,
        "size": size,
        "relpath": relpath,
        "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
    }
    mock_check_params = MagicMock()
    mock_check_params.return_value.__aenter__ = AsyncMock(
        return_value={"token": token, "dst_dir": dst_dir}
    )
    mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
    return request, patch("ai.backend.storage.api.client.check_params", mock_check_params)


class TestUploadDestination:
    @pytest.mark.parametrize(
        ("relpath", "dst_dir", "expected"),
        [
            ("file.txt", None, "file.txt"),
            ("a/b/file.txt", None, "a/b/file.txt"),
            ("file.txt", "sub/dir", "sub/dir/file.txt"),
            ("b/file.txt", "a", "a/b/file.txt"),
            ("a/../file.txt", None, "file.txt"),
        ],
    )
    async def test_upload_inside_vfolder_lands_on_destination(
        self,
        vfolder: Path,
        staging_file: Path,
        relpath: str,
        dst_dir: str | None,
        expected: str,
    ) -> None:
        request, check_params_patch = _upload_request(vfolder, relpath=relpath, dst_dir=dst_dir)

        with check_params_patch:
            response = await tus_upload_part(request)

        assert response.status == 204
        assert (vfolder / expected).read_bytes() == _PAYLOAD
        assert not staging_file.exists()

    @pytest.mark.parametrize(
        ("relpath", "dst_dir"),
        [
            ("../escaped.txt", None),
            ("a/../../escaped.txt", None),
            ("escaped.txt", ".."),
            ("../../escaped.txt", "a"),
            ("x/../../escaped.txt", "a/.."),
            (".", None),
            ("a/..", None),
        ],
    )
    async def test_upload_outside_vfolder_is_refused_before_reading_body(
        self,
        vfolder: Path,
        staging_file: Path,
        relpath: str,
        dst_dir: str | None,
    ) -> None:
        request, check_params_patch = _upload_request(vfolder, relpath=relpath, dst_dir=dst_dir)

        with check_params_patch, pytest.raises(InvalidSubpathError):
            await tus_upload_part(request)

        request.content.read.assert_not_awaited()
        assert staging_file.read_bytes() == _PAYLOAD
        assert not (vfolder.parent / "escaped.txt").exists()

    async def test_absolute_dst_dir_is_refused(
        self, vfolder: Path, staging_file: Path, outside: Path
    ) -> None:
        request, check_params_patch = _upload_request(
            vfolder, relpath="escaped.txt", dst_dir=str(outside)
        )

        with check_params_patch, pytest.raises(InvalidSubpathError):
            await tus_upload_part(request)

        assert list(outside.iterdir()) == []

    async def test_symlink_to_outside_in_destination_is_refused(
        self, vfolder: Path, staging_file: Path, outside: Path
    ) -> None:
        (vfolder / "link").symlink_to(outside)
        request, check_params_patch = _upload_request(vfolder, relpath="link/escaped.txt")

        with check_params_patch, pytest.raises(InvalidSubpathError):
            await tus_upload_part(request)

        assert list(outside.iterdir()) == []

    async def test_symlink_to_directory_inside_vfolder_is_followed(
        self, vfolder: Path, staging_file: Path
    ) -> None:
        (vfolder / "real").mkdir()
        (vfolder / "link").symlink_to(vfolder / "real")
        request, check_params_patch = _upload_request(vfolder, relpath="link/file.txt")

        with check_params_patch:
            await tus_upload_part(request)

        assert (vfolder / "real" / "file.txt").read_bytes() == _PAYLOAD

    @pytest.mark.parametrize("relpath", ["real", "link"])
    async def test_destination_that_is_a_directory_is_refused_and_staging_removed(
        self, vfolder: Path, staging_file: Path, relpath: str
    ) -> None:
        (vfolder / "real").mkdir()
        (vfolder / "real" / "kept.txt").write_bytes(b"kept")
        (vfolder / "link").symlink_to(vfolder / "real")
        request, check_params_patch = _upload_request(vfolder, relpath=relpath)

        with check_params_patch, pytest.raises(InvalidSubpathError):
            await tus_upload_part(request)

        assert not staging_file.exists()
        assert (vfolder / "real" / "kept.txt").read_bytes() == b"kept"
        assert (vfolder / "link").is_symlink()

    def test_directory_swapped_for_symlink_after_resolving_is_refused(
        self, vfolder: Path, staging_file: Path, outside: Path
    ) -> None:
        (vfolder / "sub").symlink_to(outside)
        resolved_before_swap = vfolder.resolve() / "sub" / "file.txt"

        with (
            patch(
                "ai.backend.storage.api.client.resolve_upload_target",
                return_value=resolved_before_swap,
            ),
            pytest.raises(InvalidSubpathError),
        ):
            _commit_upload(MagicMock(), vfolder, staging_file, "sub/file.txt", None)

        assert list(outside.iterdir()) == []
        assert staging_file.exists()


class TestStagingSymlink:
    @pytest.mark.parametrize("start_offset", [0, 3])
    async def test_staging_file_symlink_is_not_written_through(
        self, vfolder: Path, outside: Path, start_offset: int
    ) -> None:
        existing_file = outside / "existing_file"
        existing_file.write_bytes(b"original")
        upload_dir = vfolder / ".upload"
        upload_dir.mkdir()
        (upload_dir / _SESSION).symlink_to(existing_file)

        with pytest.raises(TusSessionNotFoundError):
            await _drain_into_upload_file(
                _body(), upload_dir / _SESSION, start_offset, TusSessionId(_SESSION)
            )

        assert existing_file.read_bytes() == b"original"

    @pytest.mark.parametrize("start_offset", [0, 3])
    async def test_upload_dir_symlink_is_not_written_through(
        self, vfolder: Path, outside: Path, start_offset: int
    ) -> None:
        existing_file = outside / _SESSION
        existing_file.write_bytes(b"original")
        (vfolder / ".upload").symlink_to(outside)

        with pytest.raises(TusSessionNotFoundError):
            await _drain_into_upload_file(
                _body(), vfolder / ".upload" / _SESSION, start_offset, TusSessionId(_SESSION)
            )

        assert existing_file.read_bytes() == b"original"

    @pytest.mark.parametrize("swap", ["file", "dir", "dangling"])
    async def test_patch_on_symlinked_staging_reports_missing_session(
        self, vfolder: Path, outside: Path, swap: str
    ) -> None:
        existing_file = outside / _SESSION
        existing_file.write_bytes(b"original")
        upload_dir = vfolder / ".upload"
        match swap:
            case "file":
                upload_dir.mkdir()
                (upload_dir / _SESSION).symlink_to(existing_file)
            case "dir":
                upload_dir.symlink_to(outside)
            case "dangling":
                upload_dir.symlink_to(outside / "missing")
        request, check_params_patch = _upload_request(vfolder, relpath="file.txt")

        with check_params_patch, pytest.raises(TusSessionNotFoundError):
            await tus_upload_part(request)

        assert existing_file.read_bytes() == b"original"
        assert not (vfolder / "file.txt").exists()

    def test_commit_with_symlinked_upload_dir_is_refused(
        self, vfolder: Path, outside: Path
    ) -> None:
        (outside / _SESSION).write_bytes(b"original")
        (vfolder / ".upload").symlink_to(outside)

        with pytest.raises(InvalidSubpathError):
            _commit_upload(MagicMock(), vfolder, vfolder / ".upload" / _SESSION, "file.txt", None)

        assert (outside / _SESSION).read_bytes() == b"original"
        assert not (vfolder / "file.txt").exists()


class TestCreateUploadSessionPath:
    @pytest.fixture
    def manager_request(self, vfolder: Path) -> Generator[tuple[MagicMock, MagicMock], None, None]:
        volume = MagicMock()
        volume.mangle_vfpath.return_value = vfolder
        volume.prepare_upload = AsyncMock(return_value=_SESSION)
        ctx = MagicMock()
        ctx.valkey_tus_client = AsyncMock()
        ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
        ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)
        ctx.local_config.storage_proxy.secret = "test-secret"
        ctx.local_config.storage_proxy.session_expire = timedelta(hours=1)
        request = MagicMock(spec=web.Request)
        request.app = {"ctx": ctx}
        yield request, volume

    def _params(self, relpath: str) -> MagicMock:
        check_params = MagicMock()
        check_params.return_value.__aenter__ = AsyncMock(
            return_value={
                "volume": "test-volume",
                "vfid": VFolderID(None, uuid.uuid4()),
                "relpath": PurePosixPath(relpath),
                "size": 1,
            }
        )
        check_params.return_value.__aexit__ = AsyncMock(return_value=None)
        return check_params

    @pytest.mark.parametrize("relpath", ["../escaped.txt", "a/../../escaped.txt", "."])
    async def test_path_outside_vfolder_gets_no_session(
        self, manager_request: tuple[MagicMock, MagicMock], relpath: str
    ) -> None:
        request, volume = manager_request

        with (
            patch("ai.backend.storage.api.manager.check_params", self._params(relpath)),
            patch("ai.backend.storage.api.manager.log_manager_api_entry", AsyncMock()),
            pytest.raises(InvalidSubpathError),
        ):
            await create_upload_session(request)

        volume.prepare_upload.assert_not_awaited()

    async def test_path_inside_vfolder_gets_a_token(
        self, manager_request: tuple[MagicMock, MagicMock]
    ) -> None:
        request, volume = manager_request

        with (
            patch("ai.backend.storage.api.manager.check_params", self._params("sub/file.txt")),
            patch("ai.backend.storage.api.manager.log_manager_api_entry", AsyncMock()),
        ):
            response = await create_upload_session(request)

        assert response.status == 200
        volume.prepare_upload.assert_awaited_once()
