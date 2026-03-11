"""Component tests for Resource Preset CRUD lifecycle and check_presets.

Tests create, list (get), modify, and delete operations through the
service/processor layer with a real database.  List/get verification
also goes through the HTTP API via the SDK client to confirm end-to-end
serialization.

TestCheckPresets verifies the check_presets endpoint returns presets with
allocatability flags and resource limits/occupancy for keypair and group scopes.

TestPresetPermissions verifies that regular (non-admin) users can list
and check presets.  Resource preset CRUD (create/modify/delete) is only
exposed through the legacy GraphQL API with SUPERADMIN restriction — the
REST API has no CRUD endpoints, so 403 testing for those mutations is not
applicable at the REST layer.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.infra import (
    CheckPresetsRequest,
    CheckPresetsResponse,
    ListPresetsResponse,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.resource_preset.creators import ResourcePresetCreatorSpec
from ai.backend.manager.repositories.resource_preset.updaters import ResourcePresetUpdaterSpec
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
    DeleteResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.modify_preset import (
    ModifyResourcePresetAction,
    ModifyResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.types import OptionalState

PresetFixtureData = dict[str, Any]
PresetFactory = Callable[..., Coroutine[Any, Any, PresetFixtureData]]


class TestPresetCRUD:
    """Full CRUD lifecycle for resource presets via the processor layer + real DB."""

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    async def _create_preset(
        self,
        processors: ResourcePresetProcessors,
        *,
        name: str | None = None,
        resource_slots: ResourceSlot | None = None,
        shared_memory: str | None = None,
        scaling_group_name: str | None = None,
    ) -> ResourcePresetData:
        """Create a preset through the processor and return the data."""
        if name is None:
            name = f"test-crud-{uuid.uuid4().hex[:8]}"
        if resource_slots is None:
            resource_slots = ResourceSlot({"cpu": "2", "mem": "2147483648"})

        action = CreateResourcePresetAction(
            creator=Creator(
                spec=ResourcePresetCreatorSpec(
                    name=name,
                    resource_slots=resource_slots,
                    shared_memory=shared_memory,
                    scaling_group_name=scaling_group_name,
                )
            )
        )
        result = await processors.create_preset.wait_for_complete(action)
        return result.resource_preset

    async def _list_presets_via_processor(
        self,
        processors: ResourcePresetProcessors,
        access_key: str,
        scaling_group: str | None = None,
    ) -> list[Any]:
        """List presets through the processor layer."""
        action = ListResourcePresetsAction(
            access_key=access_key,
            scaling_group=scaling_group,
        )
        result = await processors.list_presets.wait_for_complete(action)
        return result.presets

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    async def test_s1_create_preset_returns_data_with_id(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        database_fixture: None,
    ) -> None:
        """S-1: Create preset with name + resource_slots → returns data with generated ID."""
        preset = await self._create_preset(
            resource_preset_processors,
            name="crud-create-s1",
            resource_slots=ResourceSlot({"cpu": "4", "mem": "4294967296"}),
        )

        assert isinstance(preset, ResourcePresetData)
        assert preset.id is not None
        assert preset.name == "crud-create-s1"
        assert preset.resource_slots["cpu"] is not None
        assert preset.resource_slots["mem"] is not None

    async def test_s2_create_preset_with_shared_memory(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        database_fixture: None,
    ) -> None:
        """S-2: Create preset with shared_memory → value persisted correctly."""
        preset = await self._create_preset(
            resource_preset_processors,
            name="crud-create-s2",
            shared_memory="1073741824",  # 1 GiB
        )

        assert preset.shared_memory == 1073741824

    # ------------------------------------------------------------------
    # GET (via list + filter)
    # ------------------------------------------------------------------

    async def test_s3_get_preset_visible_in_list(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        admin_user_fixture: Any,
        database_fixture: None,
    ) -> None:
        """S-3: Created preset appears in list_presets via SDK (end-to-end)."""
        await self._create_preset(
            resource_preset_processors,
            name="crud-get-s3",
        )

        result = await admin_registry.infra.list_presets()
        assert isinstance(result, ListPresetsResponse)
        names = [p["name"] for p in result.presets]
        assert "crud-get-s3" in names

        # Also verify through the processor directly
        presets = await self._list_presets_via_processor(
            resource_preset_processors,
            access_key=admin_user_fixture.keypair.access_key,
        )
        proc_names = [p["name"] for p in presets]
        assert "crud-get-s3" in proc_names

    async def test_s4_get_preset_has_correct_resource_slots(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        database_fixture: None,
    ) -> None:
        """S-4: Get preset by name → resource_slots match what was created."""
        await self._create_preset(
            resource_preset_processors,
            name="crud-get-s4",
            resource_slots=ResourceSlot({"cpu": "8", "mem": "8589934592"}),
        )

        result = await admin_registry.infra.list_presets()
        presets_by_name = {p["name"]: p for p in result.presets}
        assert "crud-get-s4" in presets_by_name

        preset_data = presets_by_name["crud-get-s4"]
        assert preset_data["resource_slots"]["cpu"] == "8"

    # ------------------------------------------------------------------
    # MODIFY
    # ------------------------------------------------------------------

    async def test_s5_modify_preset_name(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        database_fixture: None,
    ) -> None:
        """S-5: Modify preset name → reflected on subsequent list."""
        preset = await self._create_preset(
            resource_preset_processors,
            name="crud-modify-s5-orig",
        )

        modify_action = ModifyResourcePresetAction(
            updater=Updater(
                spec=ResourcePresetUpdaterSpec(
                    name=OptionalState.update("crud-modify-s5-new"),
                ),
                pk_value=preset.id,
            ),
            id=preset.id,
            name=None,
        )
        modify_result = await resource_preset_processors.modify_preset.wait_for_complete(
            modify_action
        )
        assert isinstance(modify_result, ModifyResourcePresetActionResult)
        assert modify_result.resource_preset.name == "crud-modify-s5-new"

        # Verify via SDK
        result = await admin_registry.infra.list_presets()
        names = [p["name"] for p in result.presets]
        assert "crud-modify-s5-new" in names
        assert "crud-modify-s5-orig" not in names

    async def test_s6_modify_preset_resource_slots(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        database_fixture: None,
    ) -> None:
        """S-6: Modify preset resource_slots → changes visible in list."""
        preset = await self._create_preset(
            resource_preset_processors,
            name="crud-modify-s6",
            resource_slots=ResourceSlot({"cpu": "2", "mem": "2147483648"}),
        )

        modify_action = ModifyResourcePresetAction(
            updater=Updater(
                spec=ResourcePresetUpdaterSpec(
                    resource_slots=OptionalState.update(
                        ResourceSlot({"cpu": "16", "mem": "17179869184"})
                    ),
                ),
                pk_value=preset.id,
            ),
            id=preset.id,
            name=None,
        )
        modify_result = await resource_preset_processors.modify_preset.wait_for_complete(
            modify_action
        )
        assert modify_result.resource_preset.resource_slots["cpu"] is not None

        # Verify via SDK
        result = await admin_registry.infra.list_presets()
        presets_by_name = {p["name"]: p for p in result.presets}
        assert presets_by_name["crud-modify-s6"]["resource_slots"]["cpu"] == "16"

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    async def test_s7_delete_preset_by_id(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        database_fixture: None,
    ) -> None:
        """S-7: Delete preset → removed from list."""
        preset = await self._create_preset(
            resource_preset_processors,
            name="crud-delete-s7",
        )

        delete_action = DeleteResourcePresetAction(
            id=preset.id,
            name=None,
        )
        delete_result = await resource_preset_processors.delete_preset.wait_for_complete(
            delete_action
        )
        assert isinstance(delete_result, DeleteResourcePresetActionResult)
        assert delete_result.resource_preset.name == "crud-delete-s7"

        # Verify removal via SDK
        result = await admin_registry.infra.list_presets()
        names = [p["name"] for p in result.presets]
        assert "crud-delete-s7" not in names

    async def test_s8_delete_preset_by_name(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        database_fixture: None,
    ) -> None:
        """S-8: Delete preset by name → removed from list."""
        await self._create_preset(
            resource_preset_processors,
            name="crud-delete-s8",
        )

        delete_action = DeleteResourcePresetAction(
            id=None,
            name="crud-delete-s8",
        )
        delete_result = await resource_preset_processors.delete_preset.wait_for_complete(
            delete_action
        )
        assert delete_result.resource_preset.name == "crud-delete-s8"

        # Verify removal via SDK
        result = await admin_registry.infra.list_presets()
        names = [p["name"] for p in result.presets]
        assert "crud-delete-s8" not in names


class TestCheckPresets:
    """Tests for check_presets with resource policy matching.

    Verifies that the check_presets endpoint returns presets with
    allocatability flags and resource limit/occupancy data for
    keypair and group scopes.
    """

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    async def _create_preset(
        self,
        processors: ResourcePresetProcessors,
        *,
        name: str | None = None,
        resource_slots: ResourceSlot | None = None,
    ) -> ResourcePresetData:
        """Create a preset through the processor and return the data."""
        if name is None:
            name = f"test-check-{uuid.uuid4().hex[:8]}"
        if resource_slots is None:
            resource_slots = ResourceSlot({"cpu": "2", "mem": "2147483648"})

        action = CreateResourcePresetAction(
            creator=Creator(
                spec=ResourcePresetCreatorSpec(
                    name=name,
                    resource_slots=resource_slots,
                    shared_memory=None,
                    scaling_group_name=None,
                )
            )
        )
        result = await processors.create_preset.wait_for_complete(action)
        return result.resource_preset

    # ------------------------------------------------------------------
    # check_presets: allocatability
    # ------------------------------------------------------------------

    async def test_s1_check_presets_returns_preset_with_allocatable(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-1: Created preset appears in check_presets with allocatable flag."""
        await self._create_preset(
            resource_preset_processors,
            name="check-s1-preset",
            resource_slots=ResourceSlot({"cpu": "4", "mem": "4294967296"}),
        )

        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        assert isinstance(result, CheckPresetsResponse)
        preset_names = [p["name"] for p in result.presets]
        assert "check-s1-preset" in preset_names

        our_preset = next(p for p in result.presets if p["name"] == "check-s1-preset")
        assert "allocatable" in our_preset
        assert isinstance(our_preset["allocatable"], bool)

    async def test_s2_check_presets_no_agents_not_allocatable(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-2: Without agents, presets should not be allocatable."""
        await self._create_preset(
            resource_preset_processors,
            name="check-s2-no-agents",
        )

        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        our_preset = next(p for p in result.presets if p["name"] == "check-s2-no-agents")
        assert our_preset["allocatable"] is False

    # ------------------------------------------------------------------
    # check_presets: resource limits and occupancy
    # ------------------------------------------------------------------

    async def test_s3_check_presets_keypair_resource_limits(
        self,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-3: Response contains keypair resource limits and occupancy as dicts."""
        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        assert isinstance(result.keypair_limits, dict)
        assert isinstance(result.keypair_using, dict)
        assert isinstance(result.keypair_remaining, dict)

    async def test_s4_check_presets_group_resource_limits(
        self,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-4: Response contains group resource limits and occupancy as dicts."""
        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        assert isinstance(result.group_limits, dict)
        assert isinstance(result.group_using, dict)
        assert isinstance(result.group_remaining, dict)

    async def test_s5_check_presets_scaling_group_data(
        self,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-5: Response contains scaling group remaining and per-SG breakdown."""
        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        assert isinstance(result.scaling_group_remaining, dict)
        assert isinstance(result.scaling_groups, dict)

    async def test_s6_check_presets_with_scaling_group_filter(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        scaling_group_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-6: check_presets with scaling_group filter returns only that SG."""
        await self._create_preset(
            resource_preset_processors,
            name="check-s6-sg-filter",
        )

        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(
                group=group_name_fixture,
                scaling_group=scaling_group_fixture,
            )
        )
        assert isinstance(result, CheckPresetsResponse)
        assert isinstance(result.presets, list)
        # When filtered, scaling_groups should contain only the specified SG
        if result.scaling_groups:
            assert scaling_group_fixture in result.scaling_groups
            assert len(result.scaling_groups) == 1

    async def test_s7_check_presets_no_sessions_zero_usage(
        self,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-7: With no active sessions, keypair and group usage should be zero-valued."""
        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        # Usage values should all be "0" (no sessions running)
        for slot_value in result.keypair_using.values():
            assert slot_value == "0"
        for slot_value in result.group_using.values():
            # Group using might be "0" or NaN (if group_resource_visibility is False)
            assert slot_value in ("0", "NaN")

    async def test_s8_check_presets_preset_contains_resource_slots(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        database_fixture: None,
    ) -> None:
        """S-8: Each preset in check_presets response contains id, name, resource_slots."""
        await self._create_preset(
            resource_preset_processors,
            name="check-s8-fields",
            resource_slots=ResourceSlot({"cpu": "8", "mem": "8589934592"}),
        )

        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        our_preset = next(p for p in result.presets if p["name"] == "check-s8-fields")
        assert "id" in our_preset
        assert "name" in our_preset
        assert "resource_slots" in our_preset
        assert "allocatable" in our_preset
        assert our_preset["resource_slots"]["cpu"] == "8"


class TestPresetPermissions:
    """Permission tests for resource preset endpoints.

    Verifies that regular (non-admin) users can list and check presets,
    as both REST endpoints use ``auth_required`` (not ``superadmin_required``).

    Note: Resource preset CRUD (create/modify/delete) is only exposed through
    the legacy GraphQL API with ``allowed_roles = (UserRole.SUPERADMIN,)``.
    The REST API has no CRUD endpoints, so 403 permission testing for
    create/modify/delete is not applicable at the REST/SDK layer.
    """

    async def test_regular_user_can_list_presets(
        self,
        user_registry: BackendAIClientRegistry,
        target_preset: PresetFixtureData,
    ) -> None:
        """Regular user can list presets (read-only access via auth_required)."""
        result = await user_registry.infra.list_presets()
        assert isinstance(result, ListPresetsResponse)
        assert isinstance(result.presets, list)
        # The pre-seeded preset should be visible to the regular user
        preset_names = [p["name"] for p in result.presets]
        assert target_preset["name"] in preset_names

    async def test_regular_user_can_check_presets(
        self,
        user_registry: BackendAIClientRegistry,
        group_name_fixture: str,
        target_preset: PresetFixtureData,
    ) -> None:
        """Regular user can check presets allocatability (auth_required)."""
        result = await user_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        assert isinstance(result, CheckPresetsResponse)
        assert isinstance(result.presets, list)
        # Response should contain resource limit/usage data
        assert isinstance(result.keypair_limits, dict)
        assert isinstance(result.keypair_using, dict)
        assert isinstance(result.keypair_remaining, dict)
