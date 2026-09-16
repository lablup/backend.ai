from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.vfs_storage import VFSStorageEntityType, VFSStorageID
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.common import GenericForbidden


def _storage(name: str) -> VFSStorageData:
    return VFSStorageData(
        id=VFSStorageID(uuid4()),
        name=name,
        host="local",
        base_path=Path("/vfs") / name,
    )


class TestVFSStorageAdapterBatchLoad:
    @pytest.fixture
    def readable(self) -> VFSStorageData:
        return _storage("readable")

    @pytest.fixture
    def denied(self) -> VFSStorageData:
        return _storage("denied")

    @pytest.fixture
    def missing_id(self) -> VFSStorageID:
        return VFSStorageID(uuid4())

    @pytest.fixture
    def denial(self) -> GenericForbidden:
        return GenericForbidden("no read on this VFS storage")

    @pytest.fixture
    def processors(
        self,
        readable: VFSStorageData,
        denied: VFSStorageData,
        missing_id: VFSStorageID,
        denial: GenericForbidden,
    ) -> MagicMock:
        processors = MagicMock()
        processors.vfs_storage.bulk_get.run = AsyncMock(
            return_value=PartialBulkResult(
                items=[
                    PartialBulkEntityResult[VFSStorageData].succeeded(readable.id, readable),
                    PartialBulkEntityResult[VFSStorageData].denied(denied.id, denial),
                    PartialBulkEntityResult[VFSStorageData].failed(
                        missing_id, EntityNotFoundError(entity_type=VFSStorageEntityType())
                    ),
                ]
            )
        )
        return processors

    @pytest.fixture
    def adapter(self, processors: MagicMock) -> VFSStorageAdapter:
        return VFSStorageAdapter(processors.vfs_storage)

    async def test_answers_per_id(
        self,
        adapter: VFSStorageAdapter,
        readable: VFSStorageData,
        denied: VFSStorageData,
        missing_id: VFSStorageID,
        denial: GenericForbidden,
    ) -> None:
        nodes = await adapter.batch_load_by_ids([readable.id, denied.id, missing_id])

        node, refused, missing = nodes
        assert node is not None and not isinstance(node, Exception)
        assert node.id == readable.id
        assert refused is denial
        assert missing is None

    async def test_no_ids_read_nothing(
        self, adapter: VFSStorageAdapter, processors: MagicMock
    ) -> None:
        assert await adapter.batch_load_by_ids([]) == []
        processors.vfs_storage.bulk_get.run.assert_not_awaited()
