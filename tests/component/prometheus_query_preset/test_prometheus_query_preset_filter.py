"""Regression tests for QueryDefinitionFilter (BA-5940).

Covers the v2 search filter fields that were previously missing or unexposed:
``category_id`` and ``AND`` / ``OR`` / ``NOT`` logical composition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    QueryDefinitionFilter,
    SearchQueryDefinitionsInput,
)

if TYPE_CHECKING:
    from tests.component.prometheus_query_preset.conftest import PresetFilterDataset


class TestQueryPresetSearchFilter:
    async def test_filter_by_category_id(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_filter_dataset: PresetFilterDataset,
    ) -> None:
        """Filtering by category_id returns only presets in that category."""
        result = await admin_v2_registry.prometheus_query_preset.search(
            SearchQueryDefinitionsInput(
                filter=QueryDefinitionFilter(
                    category_id=UUIDFilter(equals=preset_filter_dataset.category_a_id)
                ),
                limit=100,
            )
        )
        assert {item.id for item in result.items} == {
            preset_filter_dataset.cpu_usage_id,
            preset_filter_dataset.cpu_memory_id,
        }

    async def test_filter_and_combines_conditions(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_filter_dataset: PresetFilterDataset,
    ) -> None:
        """AND yields the intersection of its sub-filters."""
        result = await admin_v2_registry.prometheus_query_preset.search(
            SearchQueryDefinitionsInput(
                filter=QueryDefinitionFilter(
                    AND=[
                        QueryDefinitionFilter(
                            category_id=UUIDFilter(equals=preset_filter_dataset.category_a_id)
                        ),
                        QueryDefinitionFilter(
                            name=StringFilter(equals=preset_filter_dataset.cpu_usage_name)
                        ),
                    ]
                ),
                limit=100,
            )
        )
        assert {item.id for item in result.items} == {preset_filter_dataset.cpu_usage_id}

    async def test_filter_or_combines_conditions(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_filter_dataset: PresetFilterDataset,
    ) -> None:
        """OR yields the union of its sub-filters."""
        result = await admin_v2_registry.prometheus_query_preset.search(
            SearchQueryDefinitionsInput(
                filter=QueryDefinitionFilter(
                    OR=[
                        QueryDefinitionFilter(
                            name=StringFilter(equals=preset_filter_dataset.cpu_usage_name)
                        ),
                        QueryDefinitionFilter(
                            name=StringFilter(equals=preset_filter_dataset.memory_usage_name)
                        ),
                    ]
                ),
                limit=100,
            )
        )
        assert {item.id for item in result.items} == {
            preset_filter_dataset.cpu_usage_id,
            preset_filter_dataset.memory_usage_id,
        }

    async def test_filter_not_excludes_matching(
        self,
        admin_v2_registry: V2ClientRegistry,
        preset_filter_dataset: PresetFilterDataset,
    ) -> None:
        """NOT excludes presets matching its sub-filters.

        Scoped to the seeded category to avoid coupling to other rows that
        may exist on the shared test database.
        """
        result = await admin_v2_registry.prometheus_query_preset.search(
            SearchQueryDefinitionsInput(
                filter=QueryDefinitionFilter(
                    category_id=UUIDFilter(equals=preset_filter_dataset.category_a_id),
                    NOT=[
                        QueryDefinitionFilter(
                            name=StringFilter(equals=preset_filter_dataset.cpu_memory_name)
                        ),
                    ],
                ),
                limit=100,
            )
        )
        assert {item.id for item in result.items} == {preset_filter_dataset.cpu_usage_id}
