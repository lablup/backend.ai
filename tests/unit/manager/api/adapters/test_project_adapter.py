"""The project DataLoader path: each project is answered for."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.data.project.types import ProjectData, ProjectType
from ai.backend.manager.errors.common import GenericForbidden

READABLE = ProjectID(uuid4())
DENIED = ProjectID(uuid4())
ABSENT = ProjectID(uuid4())


@pytest.fixture
def readable() -> ProjectData:
    return ProjectData(
        id=READABLE,
        name="readable",
        description=None,
        is_active=True,
        created_at=None,
        modified_at=None,
        integration_name=None,
        domain_name="default",
        total_resource_slots=ResourceSlot(),
        allowed_vfolder_hosts=VFolderHostPermissionMap(),
        dotfiles=b"",
        resource_policy="default",
        type=ProjectType.GENERAL,
        container_registry=None,
    )


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this project")


@pytest.fixture
def processors(readable: ProjectData, denial: GenericForbidden) -> MagicMock:
    processors = MagicMock()
    processors.bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[ProjectData].succeeded(READABLE, readable),
                PartialBulkEntityResult[ProjectData].denied(DENIED, denial),
                PartialBulkEntityResult[ProjectData].nothing(ABSENT),
            ]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ProjectAdapter:
    return ProjectAdapter(processors, MagicMock(), MagicMock(), MagicMock())


async def test_batch_load_answers_per_id(
    adapter: ProjectAdapter,
    denial: GenericForbidden,
) -> None:
    node, refused, missing = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert refused is denial
    assert missing is None


async def test_no_ids_read_nothing(adapter: ProjectAdapter, processors: MagicMock) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.bulk_get.run.assert_not_awaited()
