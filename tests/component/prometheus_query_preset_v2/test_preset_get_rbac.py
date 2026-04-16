"""Component tests for v2 Prometheus Query Preset GET endpoint RBAC validation.

Tests that the v2 GET /prometheus-query-presets/{id} endpoint enforces RBAC:
- Regular users WITHOUT permission are denied (403)
- Regular users WITH explicit READ permission can access (200)
- Superadmin bypasses RBAC and can access any preset (200)
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

    async def test_regular_user_without_permission_gets_403(
        self,
        user_v2_registry: V2ClientRegistry,
        preset_a: PresetFixtureData,
    ) -> None:
        """Regular user without RBAC permission cannot GET a preset."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.prometheus_query_preset.get(
                preset_a.id,
            )

    async def test_regular_user_with_read_permission_gets_200(
        self,
        user_v2_registry: V2ClientRegistry,
        preset_a: PresetFixtureData,
        grant_user_read_on_preset: None,
    ) -> None:
        """Regular user with explicit READ RBAC permission can GET a preset."""
        result = await user_v2_registry.prometheus_query_preset.get(
            preset_a.id,
        )
        assert result.item is not None
        assert result.item.id == preset_a.id

    async def test_superadmin_can_get_any_preset(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_a: PresetFixtureData,
        preset_b: PresetFixtureData,
        preset_c: PresetFixtureData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET any preset."""
        for preset in (preset_a, preset_b, preset_c):
            result = await admin_v2_registry.prometheus_query_preset.get(
                preset.id,
            )
            assert result.item is not None
            assert result.item.id == preset.id

    async def test_superadmin_querying_nonexistent_preset_gets_404(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Superadmin bypasses RBAC but gets 404 for nonexistent preset."""
        with pytest.raises(NotFoundError):
            await admin_v2_registry.prometheus_query_preset.get(uuid.uuid4())
