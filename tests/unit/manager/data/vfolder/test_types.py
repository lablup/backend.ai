from __future__ import annotations

import pytest

from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.vfolder.types import VFolderMountPermission


class TestVFolderMountPermissionFromRbac:
    @pytest.mark.parametrize(
        ("permission", "expected"),
        [
            (Permission.READ, VFolderMountPermission.READ_ONLY),
            (Permission.READ | Permission.UPDATE, VFolderMountPermission.READ_WRITE),
            (
                Permission.READ | Permission.UPDATE | Permission.SOFT_DELETE,
                VFolderMountPermission.READ_WRITE,
            ),
            (Permission.full(), VFolderMountPermission.RW_DELETE),
        ],
    )
    def test_maps_bits_to_mount_permission(
        self, permission: Permission, expected: VFolderMountPermission
    ) -> None:
        assert VFolderMountPermission.from_rbac(permission) is expected
