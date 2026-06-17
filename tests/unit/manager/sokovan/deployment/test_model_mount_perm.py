import uuid

import pytest

from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import MountPermission
from ai.backend.manager.errors.storage import VFolderPermissionError
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController

_VFOLDER_ID = VFolderUUID(uuid.uuid4())


class TestGroundModelMountPerm:
    """Model vfolder permission grounded against the requester's own permission.

    ``None`` (deployment create / revision add without an explicit permission)
    adopts the requester's effective permission; a forced ``READ_ONLY`` (vfolder
    / model-card deploy) always passes; a user-supplied value exceeding the
    requester's permission is rejected fail-fast.
    """

    def test_inherits_effective_when_unspecified(self) -> None:
        resolved = DeploymentController._ground_model_mount_perm(
            _VFOLDER_ID, None, MountPermission.READ_WRITE
        )
        assert resolved == MountPermission.READ_WRITE

    def test_forced_read_only_always_passes(self) -> None:
        resolved = DeploymentController._ground_model_mount_perm(
            _VFOLDER_ID, MountPermission.READ_ONLY, MountPermission.READ_ONLY
        )
        assert resolved == MountPermission.READ_ONLY

    def test_passes_through_when_within_effective(self) -> None:
        resolved = DeploymentController._ground_model_mount_perm(
            _VFOLDER_ID, MountPermission.READ_ONLY, MountPermission.RW_DELETE
        )
        assert resolved == MountPermission.READ_ONLY

    def test_rejects_when_request_exceeds_effective(self) -> None:
        with pytest.raises(VFolderPermissionError):
            DeploymentController._ground_model_mount_perm(
                _VFOLDER_ID, MountPermission.READ_WRITE, MountPermission.READ_ONLY
            )
