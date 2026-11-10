"""The mount level one user gets on one folder."""

from __future__ import annotations

import uuid

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import VFolderMountPolicy
from ai.backend.manager.repositories.vfolder.mount_policy import resolve_mount_policy

_READ_WRITE_BITS = Permission.READ | Permission.UPDATE


class TestResolveMountPolicy:
    def test_no_read_access_mounts_nothing(self) -> None:
        user_id = uuid.uuid4()
        assert (
            resolve_mount_policy(
                user_id,
                owner_user_id=None,
                default_mount_permission=VFolderMountPolicy.READ_WRITE,
                held=Permission.NONE,
                user_policy=VFolderMountPolicy.READ_WRITE,
            )
            == VFolderMountPolicy.NONE
        )

    def test_the_owner_mounts_read_write_regardless(self) -> None:
        user_id = uuid.uuid4()
        assert (
            resolve_mount_policy(
                user_id,
                owner_user_id=user_id,
                default_mount_permission=VFolderMountPolicy.NONE,
                held=Permission.READ,
                user_policy=VFolderMountPolicy.READ_ONLY,
            )
            == VFolderMountPolicy.READ_WRITE
        )

    def test_the_users_row_answers_before_the_default(self) -> None:
        assert (
            resolve_mount_policy(
                uuid.uuid4(),
                owner_user_id=uuid.uuid4(),
                default_mount_permission=VFolderMountPolicy.READ_WRITE,
                held=_READ_WRITE_BITS,
                user_policy=VFolderMountPolicy.NONE,
            )
            == VFolderMountPolicy.NONE
        )

    def test_the_default_answers_without_a_row(self) -> None:
        assert (
            resolve_mount_policy(
                uuid.uuid4(),
                owner_user_id=None,
                default_mount_permission=VFolderMountPolicy.READ_ONLY,
                held=_READ_WRITE_BITS,
                user_policy=None,
            )
            == VFolderMountPolicy.READ_ONLY
        )

    def test_access_bits_do_not_raise_the_level(self) -> None:
        assert (
            resolve_mount_policy(
                uuid.uuid4(),
                owner_user_id=None,
                default_mount_permission=VFolderMountPolicy.READ_ONLY,
                held=Permission.full(),
                user_policy=None,
            )
            == VFolderMountPolicy.READ_ONLY
        )
