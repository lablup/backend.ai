"""REST v2 write routes of the query-preset catalog under their base names.

The entity gate is not wired here; who may write is covered by the scenario tables.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ModifyQueryDefinitionInput,
    PartialBulkPurgeQueryDefinitionsInput,
    PartialBulkUpdateQueryDefinitionItemInput,
    PartialBulkUpdateQueryDefinitionsInput,
    SearchQueryDefinitionsInput,
)

if TYPE_CHECKING:
    from tests.component.prometheus_query_preset.conftest import PresetFilterDataset


class TestQueryPresetPurge:
    async def test_admin_purges_preset(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_filter_dataset: PresetFilterDataset,
    ) -> None:
        result = await admin_v2_registry.prometheus_query_preset.purge(
            preset_filter_dataset.cpu_usage_id
        )

        assert result.id == preset_filter_dataset.cpu_usage_id
        remaining = await admin_v2_registry.prometheus_query_preset.search(
            SearchQueryDefinitionsInput(limit=100)
        )
        assert preset_filter_dataset.cpu_usage_id not in {item.id for item in remaining.items}


class TestQueryPresetPartialBulk:
    async def test_admin_updates_several_presets(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_filter_dataset: PresetFilterDataset,
    ) -> None:
        ids = [preset_filter_dataset.cpu_usage_id, preset_filter_dataset.memory_usage_id]

        result = await admin_v2_registry.prometheus_query_preset.partial_bulk_update(
            PartialBulkUpdateQueryDefinitionsInput(
                items=[
                    PartialBulkUpdateQueryDefinitionItemInput(
                        id=preset_id, input=ModifyQueryDefinitionInput(description="bulk")
                    )
                    for preset_id in ids
                ]
            )
        )

        assert [(node.id, node.description) for node in result.successes] == [
            (preset_id, "bulk") for preset_id in ids
        ]
        assert result.failed == []

    async def test_admin_purges_several_presets_and_hears_of_the_missing_one(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_filter_dataset: PresetFilterDataset,
    ) -> None:
        missing = uuid.uuid4()

        result = await admin_v2_registry.prometheus_query_preset.partial_bulk_purge(
            PartialBulkPurgeQueryDefinitionsInput(
                ids=[preset_filter_dataset.cpu_memory_id, missing]
            )
        )

        assert [node.id for node in result.successes] == [preset_filter_dataset.cpu_memory_id]
        assert [failure.id for failure in result.failed] == [missing]
