"""The legacy ``permission`` field answers the caller's mount level, not the folder default."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.gql_legacy.base import DataLoaderManager
from ai.backend.manager.api.gql_legacy.vfolder import VirtualFolder, VirtualFolderNode
from ai.backend.manager.services.vfolder.actions.bulk_load_mount_levels import (
    BulkLoadVFolderMountLevelsAction,
)


def _levels(
    levels: dict[uuid.UUID, VFolderMountPolicy],
) -> PartialBulkResult[VFolderMountPolicy]:
    return PartialBulkResult(
        items=[
            PartialBulkEntityResult[VFolderMountPolicy].succeeded(VFolderUUID(vid), level)
            for vid, level in levels.items()
        ]
    )


class TestLegacyVFolderPermission:
    @pytest.fixture
    def run(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def info(self, run: AsyncMock) -> graphene.ResolveInfo:
        ctx = MagicMock()
        ctx.dataloader_manager = DataLoaderManager()
        ctx.processors.vfolder.bulk_load_mount_levels.run = run
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

    async def test_a_node_answers_the_callers_level(
        self, info: graphene.ResolveInfo, run: AsyncMock
    ) -> None:
        vfolder_id = uuid.uuid4()
        run.return_value = _levels({vfolder_id: VFolderMountPolicy.READ_WRITE})

        permission = await VirtualFolderNode(row_id=vfolder_id).resolve_permission(info)

        assert permission == "rw"

    async def test_a_level_of_none_answers_null(
        self, info: graphene.ResolveInfo, run: AsyncMock
    ) -> None:
        vfolder_id = uuid.uuid4()
        run.return_value = _levels({vfolder_id: VFolderMountPolicy.NONE})

        permission = await VirtualFolder(id=vfolder_id).resolve_permission(info)

        assert permission is None

    async def test_a_folder_left_out_of_the_result_answers_null(
        self, info: graphene.ResolveInfo, run: AsyncMock
    ) -> None:
        run.return_value = _levels({})

        permission = await VirtualFolder(id=uuid.uuid4()).resolve_permission(info)

        assert permission is None

    async def test_folders_resolved_together_load_in_one_call(
        self, info: graphene.ResolveInfo, run: AsyncMock
    ) -> None:
        read_only, read_write = uuid.uuid4(), uuid.uuid4()
        run.return_value = _levels({
            read_only: VFolderMountPolicy.READ_ONLY,
            read_write: VFolderMountPolicy.READ_WRITE,
        })

        permissions = await asyncio.gather(
            VirtualFolderNode(row_id=read_only).resolve_permission(info),
            VirtualFolder(id=read_write).resolve_permission(info),
        )

        assert list(permissions) == ["ro", "rw"]
        run.assert_awaited_once_with(
            BulkLoadVFolderMountLevelsAction(
                vfolder_ids=[VFolderUUID(read_only), VFolderUUID(read_write)]
            )
        )
