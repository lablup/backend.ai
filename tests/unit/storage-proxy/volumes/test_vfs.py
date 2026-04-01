from __future__ import annotations

import tempfile
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.storage.errors import QuotaScopeCreationFailedError
from ai.backend.storage.types import VFolderID
from ai.backend.storage.volumes.vfs import BaseVolume

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd


class TestBaseVolume:
    """Regression tests for BaseVolume methods."""

    @pytest.fixture
    def temp_volume_path(self) -> Iterator[Path]:
        with tempfile.TemporaryDirectory(prefix="bai-vfs-test-") as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    async def base_volume(
        self,
        temp_volume_path: Path,
        mock_etcd: AsyncEtcd,
    ) -> AsyncIterator[BaseVolume]:
        mock_event_dispatcher = MagicMock()
        mock_event_producer = MagicMock()
        volume = BaseVolume(
            {
                "storage-proxy": {
                    "scandir-limit": 1000,
                },
            },
            temp_volume_path,
            etcd=mock_etcd,
            options={},
            event_dispatcher=mock_event_dispatcher,
            event_producer=mock_event_producer,
        )
        await volume.init()
        try:
            yield volume
        finally:
            await volume.shutdown()

    @pytest.fixture
    def sample_vfolder_id(self) -> VFolderID:
        qsid = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
        return VFolderID(qsid, uuid.uuid4())

    @pytest.fixture
    async def sample_vfolder(
        self,
        base_volume: BaseVolume,
        sample_vfolder_id: VFolderID,
    ) -> AsyncIterator[VFolderID]:
        assert sample_vfolder_id.quota_scope_id is not None
        await base_volume.quota_model.create_quota_scope(sample_vfolder_id.quota_scope_id)
        await base_volume.create_vfolder(sample_vfolder_id)
        yield sample_vfolder_id
        await base_volume.delete_vfolder(sample_vfolder_id)
        await base_volume.quota_model.delete_quota_scope(sample_vfolder_id.quota_scope_id)

    @pytest.fixture
    async def dst_vfolder_id(
        self,
        base_volume: BaseVolume,
    ) -> AsyncIterator[VFolderID]:
        dst_qsid = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
        dst_vfid = VFolderID(dst_qsid, uuid.uuid4())
        yield dst_vfid
        try:
            await base_volume.delete_vfolder(dst_vfid)
        except FileNotFoundError:
            pass
        try:
            await base_volume.quota_model.delete_quota_scope(dst_qsid)
        except FileNotFoundError:
            pass

    async def test_add_file_writes_content_correctly(
        self,
        base_volume: BaseVolume,
        sample_vfolder: VFolderID,
    ) -> None:
        """
        Regression test for add_file method.

        Verifies that add_file correctly writes file content using
        run_in_executor without create_task wrapper.
        """
        test_content = b"Hello, Backend.AI!"
        relpath = PurePosixPath("test_file.txt")

        async def payload_iterator() -> AsyncIterator[bytes]:
            yield test_content

        await base_volume.add_file(sample_vfolder, relpath, payload_iterator())

        # Verify file was written correctly
        written_path = base_volume.sanitize_vfpath(sample_vfolder, relpath)
        assert written_path.exists()
        assert written_path.read_bytes() == test_content

    @pytest.mark.parametrize(
        "file_name, file_content",
        [
            ("data.txt", "clone me"),
        ],
    )
    async def test_clone_vfolder_auto_creates_quota_scope(
        self,
        base_volume: BaseVolume,
        sample_vfolder: VFolderID,
        dst_vfolder_id: VFolderID,
        file_name: str,
        file_content: str,
    ) -> None:
        """
        Regression test: clone_vfolder auto-creates the target quota scope
        when it does not exist yet.
        """
        src_vfpath = base_volume.mangle_vfpath(sample_vfolder)
        (src_vfpath / file_name).write_text(file_content)

        dst_qsid = dst_vfolder_id.quota_scope_id
        assert dst_qsid is not None

        # Quota scope does not exist yet
        assert await base_volume.quota_model.describe_quota_scope(dst_qsid) is None

        # clone_vfolder should auto-create the quota scope and succeed
        await base_volume.clone_vfolder(sample_vfolder, dst_vfolder_id)

        # Verify quota scope was created
        assert await base_volume.quota_model.describe_quota_scope(dst_qsid) is not None

        # Verify the file was copied
        dst_vfpath = base_volume.mangle_vfpath(dst_vfolder_id)
        assert (dst_vfpath / file_name).read_text() == file_content

    @pytest.mark.parametrize(
        "file_name, file_content",
        [
            ("existing.txt", "hello"),
        ],
    )
    async def test_clone_vfolder_existing_quota_scope(
        self,
        base_volume: BaseVolume,
        sample_vfolder: VFolderID,
        dst_vfolder_id: VFolderID,
        file_name: str,
        file_content: str,
    ) -> None:
        """
        Regression test: clone_vfolder works when the target quota scope
        already exists (no duplicate creation attempt).
        """
        src_vfpath = base_volume.mangle_vfpath(sample_vfolder)
        (src_vfpath / file_name).write_text(file_content)

        # Pre-create the destination quota scope
        dst_qsid = dst_vfolder_id.quota_scope_id
        assert dst_qsid is not None
        await base_volume.quota_model.create_quota_scope(dst_qsid)

        await base_volume.clone_vfolder(sample_vfolder, dst_vfolder_id)

        dst_vfpath = base_volume.mangle_vfpath(dst_vfolder_id)
        assert (dst_vfpath / file_name).read_text() == file_content

    async def test_clone_vfolder_raises_creation_failed_on_quota_scope_error(
        self,
        base_volume: BaseVolume,
        sample_vfolder: VFolderID,
        dst_vfolder_id: VFolderID,
    ) -> None:
        """clone_vfolder raises QuotaScopeCreationFailedError when create_quota_scope fails."""
        mock_create = AsyncMock(side_effect=OSError("disk full"))
        with patch.object(base_volume.quota_model, "create_quota_scope", mock_create):
            with pytest.raises(QuotaScopeCreationFailedError):
                await base_volume.clone_vfolder(sample_vfolder, dst_vfolder_id)
