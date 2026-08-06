"""Component tests for the REST v2 app config allow-list routes.

Every route carries ``superadmin_required``, so what shows only at this layer is who the
middleware admits and that the scope kind and rank survive the round trip. Rank semantics —
what the merge does with the number — belong to the repository and service unit tests.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_allow_list.request import (
    CreateAppConfigAllowListInput,
    SearchAppConfigAllowListInput,
    UpdateAppConfigAllowListInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput,
)


@pytest.fixture()
async def defined_config_name(
    admin_v2_registry: V2ClientRegistry,
    registered_config_name: str,
) -> AsyncIterator[str]:
    """An allow-list entry needs a registered config name to point at."""
    await admin_v2_registry.app_config_definition.admin_create(
        CreateAppConfigDefinitionInput(config_name=registered_config_name)
    )
    yield registered_config_name


class TestSuperadminGate:
    async def test_a_regular_user_cannot_register_an_entry(
        self,
        user_v2_registry: V2ClientRegistry,
        defined_config_name: str,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.app_config_allow_list.admin_create(
                CreateAppConfigAllowListInput(
                    config_name=defined_config_name,
                    scope_type=AppConfigScopeType.USER,
                    rank=300,
                )
            )

    async def test_a_regular_user_cannot_search_entries(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.app_config_allow_list.admin_search(
                SearchAppConfigAllowListInput(limit=1)
            )

    async def test_a_regular_user_cannot_change_a_rank(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        """The gate answers before the id is looked up, so a made-up id still gets 403."""
        entry_id = uuid.uuid4()
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.app_config_allow_list.admin_update(
                entry_id, UpdateAppConfigAllowListInput(id=entry_id, rank=1)
            )

    async def test_a_regular_user_cannot_purge_an_entry(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.app_config_allow_list.admin_purge(uuid.uuid4())


class TestAllowListRoundTrip:
    async def test_a_registered_entry_keeps_its_scope_and_rank(
        self,
        admin_v2_registry: V2ClientRegistry,
        defined_config_name: str,
    ) -> None:
        created = await admin_v2_registry.app_config_allow_list.admin_create(
            CreateAppConfigAllowListInput(
                config_name=defined_config_name,
                scope_type=AppConfigScopeType.DOMAIN,
                rank=250,
            )
        )

        fetched = await admin_v2_registry.app_config_allow_list.admin_get(
            created.app_config_allow_list.id
        )

        assert fetched.config_name == defined_config_name
        assert fetched.scope_type is AppConfigScopeType.DOMAIN
        assert fetched.rank == 250

    async def test_an_updated_rank_is_readable_back(
        self,
        admin_v2_registry: V2ClientRegistry,
        defined_config_name: str,
    ) -> None:
        created = await admin_v2_registry.app_config_allow_list.admin_create(
            CreateAppConfigAllowListInput(
                config_name=defined_config_name,
                scope_type=AppConfigScopeType.USER,
                rank=300,
            )
        )
        entry_id = created.app_config_allow_list.id

        updated = await admin_v2_registry.app_config_allow_list.admin_update(
            entry_id, UpdateAppConfigAllowListInput(id=entry_id, rank=350)
        )

        assert updated.app_config_allow_list.rank == 350
        assert (await admin_v2_registry.app_config_allow_list.admin_get(entry_id)).rank == 350

    async def test_a_purged_entry_is_gone(
        self,
        admin_v2_registry: V2ClientRegistry,
        defined_config_name: str,
    ) -> None:
        created = await admin_v2_registry.app_config_allow_list.admin_create(
            CreateAppConfigAllowListInput(
                config_name=defined_config_name,
                scope_type=AppConfigScopeType.PUBLIC,
                rank=100,
            )
        )
        entry_id = created.app_config_allow_list.id

        purged = await admin_v2_registry.app_config_allow_list.admin_purge(entry_id)

        assert purged.id == entry_id
        with pytest.raises(NotFoundError):
            await admin_v2_registry.app_config_allow_list.admin_get(entry_id)
