"""Component tests for the REST v2 app config definition routes.

The registry rules themselves are asserted in the repository and service unit tests.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    AppConfigDefinitionFilter,
    CreateAppConfigDefinitionInput,
    SearchAppConfigDefinitionsInput,
)


class TestSuperadminGate:
    async def test_every_route_turns_a_regular_user_away(
        self,
        user_v2_registry: V2ClientRegistry,
        registered_config_name: str,
    ) -> None:
        """Each route carries the gate of its own, so a route registered without it is a hole.

        The ids are made up: the gate answers before anything is looked up.
        """
        client = user_v2_registry.app_config_definition
        with pytest.raises(PermissionDeniedError):
            await client.admin_create(
                CreateAppConfigDefinitionInput(config_name=registered_config_name)
            )
        with pytest.raises(PermissionDeniedError):
            await client.admin_search(SearchAppConfigDefinitionsInput(limit=1))
        with pytest.raises(PermissionDeniedError):
            await client.admin_get(uuid.uuid4())
        with pytest.raises(PermissionDeniedError):
            await client.admin_purge(uuid.uuid4())


class TestDefinitionCRUD:
    async def test_a_registered_definition_is_readable_by_id(
        self,
        admin_v2_registry: V2ClientRegistry,
        registered_config_name: str,
    ) -> None:
        """A definition registered over REST comes back from the get route unchanged."""
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
        """The search route reaches the same row through a config-name filter."""
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
        """The purge route removes it, and the get route then reports it missing."""
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
