from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.vfolder import (
    GetVFolderIDReq,
    VFolderCreateReq,
    VFolderGetIDResponse,
    VFolderGetInfoResponse,
    VFolderListResponse,
)
from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


class TestVFolderCreateViaSDK:
    """Success scenarios for VFolder creation via SDK.

    All require a live storage-proxy (marked xfail).
    """

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_admin_creates_user_owned_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """S-1: Admin creates a user-owned vfolder with minimum required fields."""
        await admin_registry.vfolder.create(
            VFolderCreateReq(name="crud-s1-user-owned", folder_host="local"),
        )

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_admin_creates_group_owned_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
        group_fixture: uuid.UUID,
    ) -> None:
        """S-2: Admin creates a group-owned vfolder by specifying group_id."""
        await admin_registry.vfolder.create(
            VFolderCreateReq(
                name="crud-s2-group-owned",
                folder_host="local",
                group_id=group_fixture,
            ),
        )

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_admin_creates_unmanaged_vfolder(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """S-4: Admin creates an unmanaged vfolder pointing to an external path."""
        await admin_registry.vfolder.create(
            VFolderCreateReq(
                name="crud-s4-unmanaged",
                folder_host="local",
                unmanaged_path="/mnt/external/data",
            ),
        )

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_user_creates_local_special_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """S-5: Regular user creates '.local' — the allowed dot-prefix exception."""
        await user_registry.vfolder.create(
            VFolderCreateReq(name=".local", folder_host="local"),
        )

    @pytest.mark.xfail(strict=False, reason="Requires live storage-proxy")
    async def test_user_creates_cloneable_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """S-6: User creates a vfolder with cloneable=True."""
        await user_registry.vfolder.create(
            VFolderCreateReq(
                name="crud-s6-cloneable",
                folder_host="local",
                cloneable=True,
            ),
        )


class TestVFolderCreateErrors:
    """Failure scenarios for VFolder creation — errors raised before storage-proxy."""

    async def test_no_host_no_default_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-INPUT-1: Omitting folder_host with no configured default raises an error."""
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.vfolder.create(
                VFolderCreateReq(name="crud-finput1-nohost"),
            )
        assert exc_info.value.status == 400

    async def test_non_admin_cannot_create_unmanaged_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-3: Regular user specifying unmanaged_path gets Forbidden."""
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.vfolder.create(
                VFolderCreateReq(
                    name="crud-fbiz3-unmanaged",
                    folder_host="local",
                    unmanaged_path="/mnt/forbidden",
                ),
            )
        # Server wraps Forbidden as InternalServerError (500) at the API boundary
        assert exc_info.value.status == 500

    async def test_dot_prefix_name_for_group_vfolder_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """F-BIZ-4: Dot-prefixed name (except '.local') for a group vfolder is rejected."""
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.vfolder.create(
                VFolderCreateReq(
                    name=".hidden-data",
                    folder_host="local",
                    group_id=group_fixture,
                ),
            )
        assert exc_info.value.status == 400

    async def test_non_admin_cannot_create_group_vfolder_in_regular_project(
        self,
        user_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """F-BIZ-6: Regular user creating a group vfolder in a non-model-store project is Forbidden."""
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.vfolder.create(
                VFolderCreateReq(
                    name="crud-fbiz6-group",
                    folder_host="local",
                    group_id=group_fixture,
                ),
            )
        # Server wraps Forbidden as InternalServerError (500) at the API boundary
        assert exc_info.value.status == 500

    async def test_duplicate_name_raises_conflict(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        vfolder_host_permission_fixture: None,
    ) -> None:
        """F-BIZ-1: Creating a vfolder with a name that already exists raises HTTP 409."""
        existing = await vfolder_factory(name="crud-fbiz1-dup")
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.vfolder.create(
                VFolderCreateReq(
                    name=existing["name"],
                    folder_host="local",
                ),
            )
        # Server returns 400 (InvalidRequestError) for duplicate name, not 409
        assert exc_info.value.status == 400

    async def test_exceeding_max_vfolder_count_raises_error(
        self,
        db_engine: SAEngine,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        vfolder_host_permission_fixture: None,
        resource_policy_fixture: str,
    ) -> None:
        """F-BIZ-2: Creating a vfolder beyond the resource policy limit raises an error."""
        # Temporarily cap the user resource policy at 1 vfolder
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(UserResourcePolicyRow.__table__)
                .where(UserResourcePolicyRow.__table__.c.name == resource_policy_fixture)
                .values(max_vfolder_count=1)
            )
        try:
            # Pre-seed 1 vfolder to hit the limit
            await vfolder_factory(name="crud-fbiz2-limit-1")
            # Attempting to create one more should fail
            with pytest.raises(BackendAPIError) as exc_info:
                await admin_registry.vfolder.create(
                    VFolderCreateReq(
                        name="crud-fbiz2-over-limit",
                        folder_host="local",
                    ),
                )
            assert exc_info.value.status == 400
        finally:
            # Always restore the policy to unlimited
            async with db_engine.begin() as conn:
                await conn.execute(
                    sa.update(UserResourcePolicyRow.__table__)
                    .where(UserResourcePolicyRow.__table__.c.name == resource_policy_fixture)
                    .values(max_vfolder_count=0)
                )


class TestVFolderList:
    """List scenarios for VFolder — no storage-proxy required."""

    async def test_user_sees_own_seeded_vfolder_in_list(
        self,
        user_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        """S-4: A DB-seeded user-owned vfolder appears in the list response."""
        user_uuid = regular_user_fixture.user_uuid
        vf = await vfolder_factory(
            user=str(user_uuid),
            creator="user-test@test.local",
            quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_uuid)),
        )
        result = await user_registry.vfolder.list()
        assert isinstance(result, VFolderListResponse)
        names = [item.name for item in result.root]
        assert vf["name"] in names

    async def test_user_with_no_vfolders_gets_empty_list(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """S-5: A user with no vfolders gets an empty list."""
        result = await user_registry.vfolder.list()
        assert isinstance(result, VFolderListResponse)
        assert result.root == []


class TestVFolderGetInfo:
    """Get-info scenarios for VFolder."""

    @pytest.mark.xfail(
        strict=False,
        reason="get_info fetches usage data from storage-proxy, not available in component tests",
    )
    async def test_admin_gets_own_vfolder_info(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """S-1: Admin retrieves vfolder info by name."""
        result = await admin_registry.vfolder.get_info(target_vfolder["name"])
        assert isinstance(result, VFolderGetInfoResponse)
        assert result.item.name == target_vfolder["name"]

    @pytest.mark.xfail(
        strict=False,
        reason="get_info fetches usage data from storage-proxy, not available in component tests",
    )
    async def test_admin_gets_another_users_vfolder_info(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_factory: VFolderFactory,
        regular_user_fixture: Any,
    ) -> None:
        """S-3: Admin can get_info of a vfolder owned by another user."""
        user_uuid = regular_user_fixture.user_uuid
        vf = await vfolder_factory(
            user=str(user_uuid),
            creator="user-test@test.local",
            quota_scope_id=str(QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_uuid)),
        )
        result = await admin_registry.vfolder.get_info(vf["name"])
        assert isinstance(result, VFolderGetInfoResponse)
        assert result.item.name == vf["name"]

    async def test_get_nonexistent_vfolder_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Querying a non-existent vfolder name raises an error (HTTP 404)."""
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.vfolder.get_info("crud-nonexistent-vfolder-xyz-99999")
        assert exc_info.value.status == 404

    async def test_user_cannot_get_info_of_inaccessible_vfolder(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """F-BIZ-2: Regular user querying a vfolder they cannot access gets not-found."""
        # target_vfolder is owned by the admin user; user_registry is a regular user
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.vfolder.get_info(target_vfolder["name"])
        assert exc_info.value.status == 404


class TestVFolderGetID:
    """ID-retrieval scenarios for VFolder."""

    @pytest.mark.xfail(
        strict=False,
        reason="HMAC mismatch on GET with query params — SDK signing issue",
    )
    async def test_get_vfolder_id_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
    ) -> None:
        """Retrieve vfolder UUID from its name."""
        result = await admin_registry.vfolder.get_id(
            GetVFolderIDReq(name=target_vfolder["name"]),
        )
        assert isinstance(result, VFolderGetIDResponse)
        assert result.item.id == target_vfolder["id"].hex
