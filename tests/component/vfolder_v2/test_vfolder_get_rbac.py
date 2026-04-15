"""Component tests for v2 VFolder GET endpoint RBAC validation.

Tests that the v2 GET /vfolders/{id} endpoint enforces RBAC:
- Regular users WITHOUT permission are denied (403)
- Superadmin bypasses RBAC and can access vfolders directly
- Superadmin querying nonexistent vfolder gets 404 (RBAC bypassed, service returns not found)
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from .conftest import VFolderFixtureData


class TestVFolderGetV2RBAC:
    """RBAC validation for v2 GET /vfolders/{id}.

    The v2 GET endpoint uses SingleEntityActionProcessor with
    single_entity_rbac_validators. Superadmin bypasses RBAC;
    regular users without explicit permission grants are denied.
    """

    async def test_regular_user_querying_own_vfolder_gets_403(
        self,
        user_v2_registry: V2ClientRegistry,
        vfolder_owned_by_regular_user: VFolderFixtureData,
    ) -> None:
        """Regular user without RBAC permission cannot GET their own vfolder."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.vfolder.get(vfolder_owned_by_regular_user.id)

    async def test_superadmin_querying_own_vfolder_bypasses_rbac(
        self,
        admin_v2_registry: V2ClientRegistry,
        vfolder_owned_by_admin: VFolderFixtureData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET their own vfolder."""
        result = await admin_v2_registry.vfolder.get(vfolder_owned_by_admin.id)
        assert result.id == vfolder_owned_by_admin.id

    async def test_superadmin_querying_other_users_vfolder_bypasses_rbac(
        self,
        admin_v2_registry: V2ClientRegistry,
        vfolder_owned_by_regular_user: VFolderFixtureData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET other users' vfolders."""
        result = await admin_v2_registry.vfolder.get(vfolder_owned_by_regular_user.id)
        assert result.id == vfolder_owned_by_regular_user.id

    async def test_superadmin_querying_nonexistent_vfolder_gets_404(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Superadmin bypasses RBAC but gets 404 for nonexistent vfolder."""
        with pytest.raises(NotFoundError):
            await admin_v2_registry.vfolder.get(uuid.uuid4())
