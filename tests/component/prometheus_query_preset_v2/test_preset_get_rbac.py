"""Component tests for v2 Prometheus Query Preset GET endpoint RBAC validation.

Tests that the v2 GET /prometheus-query-presets/{id} endpoint enforces RBAC:
- Regular users WITHOUT permission are denied (403)
- Superadmin bypasses RBAC and can access any preset (own, others', third-party)
- Superadmin querying nonexistent preset gets 404 (RBAC bypassed, service returns not found)
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from .conftest import PresetFixtureData


class TestPresetGetV2RBAC:
    """RBAC validation for v2 GET /prometheus-query-presets/{id}.

    The v2 GET endpoint uses SingleEntityActionProcessor with
    single_entity_rbac_validators. Superadmin bypasses RBAC;
    regular users without explicit permission grants are denied.
    """

    async def test_regular_user_querying_preset_gets_403(
        self,
        user_v2_registry: V2ClientRegistry,
        preset_owned_by_admin: PresetFixtureData,
    ) -> None:
        """Regular user without RBAC permission cannot GET a preset."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.prometheus_query_preset.get(
                preset_owned_by_admin.id,
            )

    async def test_superadmin_can_get_own_preset(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_owned_by_admin: PresetFixtureData,
    ) -> None:
        """Superadmin can GET their own preset."""
        result = await admin_v2_registry.prometheus_query_preset.get(
            preset_owned_by_admin.id,
        )
        assert result.item is not None
        assert result.item.id == preset_owned_by_admin.id

    async def test_superadmin_can_get_regular_users_preset(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_owned_by_user: PresetFixtureData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET regular user's preset."""
        result = await admin_v2_registry.prometheus_query_preset.get(
            preset_owned_by_user.id,
        )
        assert result.item is not None
        assert result.item.id == preset_owned_by_user.id

    async def test_superadmin_can_get_other_users_preset(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_owned_by_other: PresetFixtureData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET third-party's preset."""
        result = await admin_v2_registry.prometheus_query_preset.get(
            preset_owned_by_other.id,
        )
        assert result.item is not None
        assert result.item.id == preset_owned_by_other.id

    async def test_superadmin_querying_nonexistent_preset_gets_404(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Superadmin bypasses RBAC but gets 404 for nonexistent preset."""
        with pytest.raises(NotFoundError):
            await admin_v2_registry.prometheus_query_preset.get(uuid.uuid4())
