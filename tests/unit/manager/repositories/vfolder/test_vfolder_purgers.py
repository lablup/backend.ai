"""
Tests for vfolder purgers functionality.
Tests the purger pattern implementation for vfolder-related deletions.
"""

from __future__ import annotations

import uuid

from ai.backend.manager.repositories.base.purger import BatchPurger
from ai.backend.manager.repositories.vfolder.purgers import (
    VFolderInvitationBatchPurgerSpec,
    VFolderPermissionBatchPurgerSpec,
    create_vfolder_invitation_purger,
    create_vfolder_permission_purger,
)


class TestVFolderPurgerFactoryFunctions:
    """Tests for purger factory functions."""

    def test_create_vfolder_invitation_purger(self) -> None:
        """Test create_vfolder_invitation_purger returns correct BatchPurger."""
        vfolder_ids = [uuid.uuid4(), uuid.uuid4()]

        purger = create_vfolder_invitation_purger(vfolder_ids)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, VFolderInvitationBatchPurgerSpec)
        assert purger.spec.vfolder_ids == vfolder_ids

    def test_create_vfolder_permission_purger(self) -> None:
        """Test create_vfolder_permission_purger returns correct BatchPurger."""
        vfolder_ids = [uuid.uuid4(), uuid.uuid4()]

        purger = create_vfolder_permission_purger(vfolder_ids)

        assert isinstance(purger, BatchPurger)
        assert isinstance(purger.spec, VFolderPermissionBatchPurgerSpec)
        assert purger.spec.vfolder_ids == vfolder_ids
