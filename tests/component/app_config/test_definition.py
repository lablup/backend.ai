"""Component tests for the REST v2 app config definition routes.

Every route carries ``superadmin_required``, so what shows only at this layer is who the
middleware admits and that the node survives the round trip. The registry rules themselves
are asserted in the repository and service unit tests.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionFilter,
    CreateAppConfigDefinitionInput,
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.query import StringFilter


class TestSuperadminGate:
    async def test_a_regular_user_cannot_register_a_definition(
        self,
        user_v2_registry: V2ClientRegistry,
        registered_config_name: str,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.app_config_definition.admin_create(
                CreateAppConfigDefinitionInput(config_name=registered_config_name)
            )

    async def test_a_regular_user_cannot_search_definitions(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.app_config_definition.admin_search(
                SearchAppConfigDefinitionsInput(limit=1)
            )

    async def test_a_regular_user_cannot_purge_a_definition(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        """The gate answers before the id is looked up, so a made-up id still gets 403."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.app_config_definition.admin_purge(uuid.uuid4())


class TestDefinitionRoundTrip:
    async def test_a_registered_definition_is_readable_by_id(
        self,
        admin_v2_registry: V2ClientRegistry,
        registered_config_name: str,
    ) -> None:
        created = await admin_v2_registry.app_config_definition.admin_create(
            CreateAppConfigDefinitionInput(config_name=registered_config_name)
        )

        fetched = await admin_v2_registry.app_config_definition.admin_get(
            created.app_config_definition.id
        )

        assert fetched.id == created.app_config_definition.id
        assert fetched.config_name == registered_config_name

    async def test_a_registered_definition_is_found_by_search(
        self,
        admin_v2_registry: V2ClientRegistry,
        registered_config_name: str,
    ) -> None:
        created = await admin_v2_registry.app_config_definition.admin_create(
            CreateAppConfigDefinitionInput(config_name=registered_config_name)
        )

        found = await admin_v2_registry.app_config_definition.admin_search(
            SearchAppConfigDefinitionsInput(
                filter=AppConfigDefinitionFilter(
                    config_name=StringFilter(equals=registered_config_name)
                ),
                limit=10,
            )
        )

        assert [node.id for node in found.items] == [created.app_config_definition.id]

    async def test_a_purged_definition_is_gone(
        self,
        admin_v2_registry: V2ClientRegistry,
        registered_config_name: str,
    ) -> None:
        created = await admin_v2_registry.app_config_definition.admin_create(
            CreateAppConfigDefinitionInput(config_name=registered_config_name)
        )

        purged = await admin_v2_registry.app_config_definition.admin_purge(
            created.app_config_definition.id
        )

        assert purged.id == created.app_config_definition.id
        with pytest.raises(NotFoundError):
            await admin_v2_registry.app_config_definition.admin_get(
                created.app_config_definition.id
            )
