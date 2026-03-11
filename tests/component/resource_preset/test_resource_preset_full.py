"""Component tests for Resource Preset CRUD lifecycle.

Tests create, list (get), modify, and delete operations through the
service/processor layer with a real database.  List/get verification
also goes through the HTTP API via the SDK client to confirm end-to-end
serialization.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.infra import ListPresetsResponse
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
        result = await processors.create_preset(action)
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
        result = await processors.list_presets(action)
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
        modify_result = await resource_preset_processors.modify_preset(modify_action)
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
        modify_result = await resource_preset_processors.modify_preset(modify_action)
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
        delete_result = await resource_preset_processors.delete_preset(delete_action)
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
        delete_result = await resource_preset_processors.delete_preset(delete_action)
        assert delete_result.resource_preset.name == "crud-delete-s8"

        # Verify removal via SDK
        result = await admin_registry.infra.list_presets()
        names = [p["name"] for p in result.presets]
        assert "crud-delete-s8" not in names

    # ------------------------------------------------------------------
    # FULL LIFECYCLE
    # ------------------------------------------------------------------

    async def test_s9_full_crud_lifecycle(
        self,
        resource_preset_processors: ResourcePresetProcessors,
        admin_registry: BackendAIClientRegistry,
        database_fixture: None,
    ) -> None:
        """S-9: Create → List → Modify → List → Delete → List (full lifecycle)."""
        # CREATE
        preset = await self._create_preset(
            resource_preset_processors,
            name="crud-lifecycle-s9",
            resource_slots=ResourceSlot({"cpu": "2", "mem": "2147483648"}),
        )
        assert preset.id is not None

        # LIST - visible
        result = await admin_registry.infra.list_presets()
        names = [p["name"] for p in result.presets]
        assert "crud-lifecycle-s9" in names

        # MODIFY
        modify_action = ModifyResourcePresetAction(
            updater=Updater(
                spec=ResourcePresetUpdaterSpec(
                    name=OptionalState.update("crud-lifecycle-s9-modified"),
                    resource_slots=OptionalState.update(
                        ResourceSlot({"cpu": "4", "mem": "4294967296"})
                    ),
                ),
                pk_value=preset.id,
            ),
            id=preset.id,
            name=None,
        )
        await resource_preset_processors.modify_preset(modify_action)

        # LIST - verify modification
        result = await admin_registry.infra.list_presets()
        names = [p["name"] for p in result.presets]
        assert "crud-lifecycle-s9-modified" in names
        assert "crud-lifecycle-s9" not in names

        presets_by_name = {p["name"]: p for p in result.presets}
        assert presets_by_name["crud-lifecycle-s9-modified"]["resource_slots"]["cpu"] == "4"

        # DELETE
        delete_action = DeleteResourcePresetAction(
            id=preset.id,
            name=None,
        )
        await resource_preset_processors.delete_preset(delete_action)

        # LIST - verify deletion
        result = await admin_registry.infra.list_presets()
        names = [p["name"] for p in result.presets]
        assert "crud-lifecycle-s9-modified" not in names
