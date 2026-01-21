from __future__ import annotations

import tempfile
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import QuotaScopeID, QuotaScopeType
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
