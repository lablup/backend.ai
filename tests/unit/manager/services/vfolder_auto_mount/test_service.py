"""The mount destination and subpath checks of VFolderAutoMountService."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.manager.data.vfolder.types import VFolderMountPermission
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountSpec
from ai.backend.manager.errors.base.entity import EntityError
from ai.backend.manager.errors.vfolder_auto_mount import (
    VFolderAutoMountDestinationReserved,
    VFolderAutoMountSubpathOutsideVFolder,
)
from ai.backend.manager.models.vfolder_auto_mount.creators import VFolderAutoMountCreator
from ai.backend.manager.models.vfolder_auto_mount.updaters import VFolderAutoMountUpdater
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.vfolder_auto_mount.repository import (
    VFolderAutoMountRepository,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.create import (
    CreateVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.update import (
    UpdateVFolderAutoMountAction,
)
from ai.backend.manager.services.vfolder_auto_mount.service import VFolderAutoMountService
from ai.backend.manager.types import OptionalState


@dataclass(frozen=True)
class _RejectedCreateCase:
    mount_destination: str
    subpath: str
    expected_error: type[EntityError]


@dataclass(frozen=True)
class _CreateSituation:
    service: VFolderAutoMountService
    repository: MagicMock
    action: CreateVFolderAutoMountAction


@dataclass(frozen=True)
class _RejectedUpdateCase:
    mount_destination: OptionalState[str]
    subpath: OptionalState[str]
    expected_error: type[EntityError]


@dataclass(frozen=True)
class _UpdateSituation:
    service: VFolderAutoMountService
    ops_repository: MagicMock
    action: UpdateVFolderAutoMountAction


class TestCreate:
    @pytest.fixture
    def create_with_a_subpath_inside_the_vfolder(self) -> _CreateSituation:
        return self._create_situation(mount_destination="/home/work/data", subpath="data/../train")

    @pytest.fixture
    def rejected_create(self, case: _RejectedCreateCase) -> _CreateSituation:
        return self._create_situation(
            mount_destination=case.mount_destination, subpath=case.subpath
        )

    async def test_registers_a_subpath_inside_the_vfolder(
        self, create_with_a_subpath_inside_the_vfolder: _CreateSituation
    ) -> None:
        situation = create_with_a_subpath_inside_the_vfolder

        await situation.service.create(situation.action)

        situation.repository.create.assert_awaited_once_with(situation.action.creator)

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedCreateCase(
                mount_destination="/home/work/.ssh",
                subpath=".",
                expected_error=VFolderAutoMountDestinationReserved,
            ),
            _RejectedCreateCase(
                mount_destination="/home/work/data",
                subpath="..",
                expected_error=VFolderAutoMountSubpathOutsideVFolder,
            ),
            _RejectedCreateCase(
                mount_destination="/home/work/data",
                subpath="../other",
                expected_error=VFolderAutoMountSubpathOutsideVFolder,
            ),
            _RejectedCreateCase(
                mount_destination="/home/work/data",
                subpath="data/../../other",
                expected_error=VFolderAutoMountSubpathOutsideVFolder,
            ),
            _RejectedCreateCase(
                mount_destination="/home/work/data",
                subpath="/data",
                expected_error=VFolderAutoMountSubpathOutsideVFolder,
            ),
        ],
        ids=[
            "reserved-destination",
            "parent-directory",
            "path-under-the-parent-directory",
            "path-leaving-the-vfolder-once-normalized",
            "absolute-path",
        ],
    )
    async def test_rejects_without_writing(
        self, case: _RejectedCreateCase, rejected_create: _CreateSituation
    ) -> None:
        with pytest.raises(case.expected_error):
            await rejected_create.service.create(rejected_create.action)

        rejected_create.repository.create.assert_not_awaited()

    def _create_situation(self, mount_destination: str, subpath: str) -> _CreateSituation:
        repository = MagicMock(spec=VFolderAutoMountRepository)
        return _CreateSituation(
            service=VFolderAutoMountService(repository, MagicMock(spec=OpsRepository)),
            repository=repository,
            action=CreateVFolderAutoMountAction(
                creator=VFolderAutoMountCreator(
                    scope=VFolderAutoMountScopeType.PROJECT.to_owner(uuid.uuid4()),
                    spec=VFolderAutoMountSpec(
                        vfolder_id=VFolderUUID(uuid.uuid4()),
                        mount_destination=mount_destination,
                        subpath=subpath,
                        mount_permission=VFolderMountPermission.READ_ONLY,
                    ),
                )
            ),
        )


class TestUpdate:
    @pytest.fixture
    def update_of_the_permission_only(self) -> _UpdateSituation:
        return self._update_situation(
            mount_destination=OptionalState.nop(), subpath=OptionalState.nop()
        )

    @pytest.fixture
    def rejected_update(self, case: _RejectedUpdateCase) -> _UpdateSituation:
        return self._update_situation(
            mount_destination=case.mount_destination, subpath=case.subpath
        )

    async def test_applies_an_update_of_the_permission_only(
        self, update_of_the_permission_only: _UpdateSituation
    ) -> None:
        situation = update_of_the_permission_only

        await situation.service.update(situation.action)

        situation.ops_repository.update.assert_awaited_once_with(situation.action.updater)

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedUpdateCase(
                mount_destination=OptionalState.update("/home/work/.ssh"),
                subpath=OptionalState.nop(),
                expected_error=VFolderAutoMountDestinationReserved,
            ),
            _RejectedUpdateCase(
                mount_destination=OptionalState.nop(),
                subpath=OptionalState.update("../other"),
                expected_error=VFolderAutoMountSubpathOutsideVFolder,
            ),
        ],
        ids=["reserved-destination", "subpath-leaving-the-vfolder"],
    )
    async def test_rejects_without_writing(
        self, case: _RejectedUpdateCase, rejected_update: _UpdateSituation
    ) -> None:
        with pytest.raises(case.expected_error):
            await rejected_update.service.update(rejected_update.action)

        rejected_update.ops_repository.update.assert_not_awaited()

    def _update_situation(
        self, mount_destination: OptionalState[str], subpath: OptionalState[str]
    ) -> _UpdateSituation:
        ops_repository = MagicMock(spec=OpsRepository)
        return _UpdateSituation(
            service=VFolderAutoMountService(
                MagicMock(spec=VFolderAutoMountRepository), ops_repository
            ),
            ops_repository=ops_repository,
            action=UpdateVFolderAutoMountAction(
                updater=VFolderAutoMountUpdater(
                    vfolder_auto_mount_id=VFolderAutoMountID(uuid.uuid4()),
                    mount_destination=mount_destination,
                    subpath=subpath,
                    mount_permission=OptionalState.update(VFolderMountPermission.READ_WRITE),
                )
            ),
        )
