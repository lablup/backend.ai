"""Who may read the query-preset catalog.

The catalog's routes declare ``auth_required`` for the reads and
``superadmin_required`` for the writes. The action layer carries its own gate, so a
read wired behind the super-admin gate turns those routes into 403s for every
regular user while the route declaration still says otherwise — a break no filter
or preview test notices, because both authenticate as an admin.
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
    async def test_user_searches_presets(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await user_v2_registry.prometheus_query_preset.search(
            SearchQueryDefinitionsInput(limit=10),
        )
        assert isinstance(result.items, list)

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
