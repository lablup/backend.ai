from __future__ import annotations

import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import MountInfoEntry, MountPermission
from ai.backend.manager.data.deployment.types import ModelMountConfigData, ModelRevisionData
from ai.backend.manager.data.vfolder.types import VFolderMountAvailability
from ai.backend.manager.errors.deployment import (
    RevisionMissingModelVFolder,
    RevisionVFolderNotMountable,
)
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)

_DEPLOYMENT_ID = DeploymentID(uuid.uuid4())
_REVISION_ID = DeploymentRevisionID(uuid.uuid4())
_MODEL_VFOLDER_ID = VFolderUUID(uuid.uuid4())
_EXTRA_VFOLDER_ID = VFolderUUID(uuid.uuid4())


def _availability(
    *,
    missing: frozenset[VFolderUUID] = frozenset(),
    trashed: frozenset[VFolderUUID] = frozenset(),
    deleted: frozenset[VFolderUUID] = frozenset(),
    not_ready: frozenset[VFolderUUID] = frozenset(),
) -> VFolderMountAvailability:
    return VFolderMountAvailability(
        missing=missing, trashed=trashed, deleted=deleted, not_ready=not_ready
    )


def _revision(model_vfolder_id: VFolderUUID | None) -> ModelRevisionData:
    revision = MagicMock(spec=ModelRevisionData)
    revision.id = _REVISION_ID
    revision.revision_number = 1
    revision.model_mount_config = ModelMountConfigData(
        vfolder_id=model_vfolder_id,
        mount_destination="/models",
        definition_path="model-definition.yaml",
        extra_mounts=[MountInfoEntry(vfolder_id=_EXTRA_VFOLDER_ID)],
        model_mount_perm=MountPermission.READ_ONLY,
    )
    return cast(ModelRevisionData, revision)


class TestActivateRevisionVFolders:
    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.get_revision = AsyncMock(return_value=_revision(_MODEL_VFOLDER_ID))
        repository.vfolder_mount_availability = AsyncMock(return_value=_availability())
        repository.get_endpoint_info = AsyncMock(
            return_value=MagicMock(current_revision_id=DeploymentRevisionID(uuid.uuid4()))
        )
        repository.activate_revision = AsyncMock(return_value=(None, True))
        repository.get_deployment_policy = AsyncMock(return_value=MagicMock())
        return repository

    @pytest.fixture
    def deployment_controller(self, mock_deployment_repository: MagicMock) -> DeploymentController:
        valkey_schedule = MagicMock()
        valkey_schedule.mark_deployment_needed = AsyncMock()
        return DeploymentController(
            DeploymentControllerArgs(
                scheduling_controller=MagicMock(),
                deployment_repository=mock_deployment_repository,
                config_provider=MagicMock(),
                storage_manager=MagicMock(),
                event_producer=MagicMock(),
                valkey_schedule=valkey_schedule,
                revision_draft_reader=MagicMock(),
                deployment_revision_preset_repository=MagicMock(),
            )
        )

    async def test_activates_revision_whose_vfolders_are_mountable(
        self,
        deployment_controller: DeploymentController,
        mock_deployment_repository: MagicMock,
    ) -> None:
        result = await deployment_controller.activate_revision(_DEPLOYMENT_ID, _REVISION_ID)

        assert result.activated_revision_id == _REVISION_ID
        mock_deployment_repository.vfolder_mount_availability.assert_awaited_once_with([
            _MODEL_VFOLDER_ID,
            _EXTRA_VFOLDER_ID,
        ])
        mock_deployment_repository.activate_revision.assert_awaited_once_with(
            _DEPLOYMENT_ID, _REVISION_ID
        )

    async def test_rejects_revision_whose_model_vfolder_was_purged(
        self,
        deployment_controller: DeploymentController,
        mock_deployment_repository: MagicMock,
    ) -> None:
        mock_deployment_repository.get_revision = AsyncMock(return_value=_revision(None))

        with pytest.raises(RevisionMissingModelVFolder):
            await deployment_controller.activate_revision(_DEPLOYMENT_ID, _REVISION_ID)

        mock_deployment_repository.activate_revision.assert_not_awaited()

    @pytest.mark.parametrize(
        ("availability", "reason", "vfolder_id"),
        [
            pytest.param(
                _availability(missing=frozenset({_MODEL_VFOLDER_ID})),
                "purged",
                _MODEL_VFOLDER_ID,
                id="model-purged",
            ),
            pytest.param(
                _availability(trashed=frozenset({_EXTRA_VFOLDER_ID})),
                "in the trash",
                _EXTRA_VFOLDER_ID,
                id="extra-mount-trashed",
            ),
            pytest.param(
                _availability(deleted=frozenset({_EXTRA_VFOLDER_ID})),
                "deleted",
                _EXTRA_VFOLDER_ID,
                id="extra-mount-deleted",
            ),
            pytest.param(
                _availability(not_ready=frozenset({_MODEL_VFOLDER_ID})),
                "not ready",
                _MODEL_VFOLDER_ID,
                id="model-not-ready",
            ),
        ],
    )
    async def test_rejects_revision_with_unmountable_vfolder(
        self,
        deployment_controller: DeploymentController,
        mock_deployment_repository: MagicMock,
        availability: VFolderMountAvailability,
        reason: str,
        vfolder_id: VFolderUUID,
    ) -> None:
        mock_deployment_repository.vfolder_mount_availability = AsyncMock(return_value=availability)

        with pytest.raises(RevisionVFolderNotMountable) as exc_info:
            await deployment_controller.activate_revision(_DEPLOYMENT_ID, _REVISION_ID)

        assert f"{reason}: ['{vfolder_id}']" in str(exc_info.value)
        mock_deployment_repository.activate_revision.assert_not_awaited()
