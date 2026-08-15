"""Who may reach the query-preset catalog.

Every route in this domain is a super-admin operation: the presets describe
cluster-wide PromQL, and executing one runs that query against the metrics
backend. The filter and preview suites all authenticate as an admin, so nothing
there would notice the gate coming off.
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    CreateQueryDefinitionOptionsInput,
    SearchQueryDefinitionsInput,
)


class TestQueryPresetCatalogAccess:
    async def test_user_cannot_search_presets(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.prometheus_query_preset.search(
                SearchQueryDefinitionsInput(limit=10),
            )

    async def test_user_cannot_create_preset(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.prometheus_query_preset.create(
                CreateQueryDefinitionInput(
                    name="user-attempted-preset",
                    metric_name="up",
                    query_template="up",
                    options=CreateQueryDefinitionOptionsInput(
                        filter_labels=[],
                        group_labels=[],
                    ),
                ),
            )

    async def test_admin_searches_presets(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.prometheus_query_preset.search(
            SearchQueryDefinitionsInput(limit=10),
        )
        assert isinstance(result.items, list)
