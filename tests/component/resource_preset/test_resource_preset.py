"""Component tests for ResourcePreset CRUD + check integration.

Tests the HTTP API layer with a real aiohttp server and real DB.
Validates the list and check flows through the SDK client.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.infra import (
    CheckPresetsRequest,
    CheckPresetsResponse,
    ListPresetsRequest,
    ListPresetsResponse,
)

PresetFixtureData = dict[str, Any]
PresetFactory = Callable[..., Coroutine[Any, Any, PresetFixtureData]]


class TestResourcePresetList:
    """Tests for listing resource presets via HTTP API."""

    async def test_admin_lists_presets_with_fixture(
        self,
        admin_registry: BackendAIClientRegistry,
        target_preset: PresetFixtureData,
    ) -> None:
        """Admin can list presets; the DB-seeded preset is visible."""
        result = await admin_registry.infra.list_presets()
        assert isinstance(result, ListPresetsResponse)
        preset_names = [p["name"] for p in result.presets]
        assert target_preset["name"] in preset_names

        # Verify resource slots are preserved through the API layer
        presets_by_name = {p["name"]: p for p in result.presets}
        preset_data = presets_by_name[target_preset["name"]]
        assert "resource_slots" in preset_data
        assert preset_data["resource_slots"]["cpu"] == "2"

    async def test_admin_lists_presets_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Listing presets returns a list when no custom presets exist."""
        result = await admin_registry.infra.list_presets()
        assert isinstance(result, ListPresetsResponse)
        assert isinstance(result.presets, list)

    async def test_admin_lists_presets_with_scaling_group_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        target_preset: PresetFixtureData,
    ) -> None:
        """Filtering by scaling group still returns system presets."""
        result = await admin_registry.infra.list_presets(
            ListPresetsRequest(scaling_group=scaling_group_fixture)
        )
        assert isinstance(result, ListPresetsResponse)
        assert isinstance(result.presets, list)


class TestResourcePresetCheck:
    """Tests for checking resource presets allocatability via HTTP API."""

    async def test_admin_checks_presets_with_group(
        self,
        admin_registry: BackendAIClientRegistry,
        target_preset: PresetFixtureData,
        group_name_fixture: str,
    ) -> None:
        """Admin checks presets; response contains allocatability details."""
        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        assert isinstance(result, CheckPresetsResponse)
        assert isinstance(result.presets, list)
        assert isinstance(result.keypair_limits, dict)
        assert isinstance(result.keypair_using, dict)
        assert isinstance(result.keypair_remaining, dict)
        assert isinstance(result.group_limits, dict)
        assert isinstance(result.group_using, dict)
        assert isinstance(result.group_remaining, dict)
        assert isinstance(result.scaling_group_remaining, dict)
        assert isinstance(result.scaling_groups, dict)

    async def test_admin_checks_presets_with_scaling_group(
        self,
        admin_registry: BackendAIClientRegistry,
        target_preset: PresetFixtureData,
        group_name_fixture: str,
        scaling_group_fixture: str,
    ) -> None:
        """Admin checks presets filtered by scaling group."""
        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(
                group=group_name_fixture,
                scaling_group=scaling_group_fixture,
            )
        )
        assert isinstance(result, CheckPresetsResponse)
        assert isinstance(result.presets, list)
