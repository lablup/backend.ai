from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.config import (
    DeleteDomainDotfileRequest,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
    GetDomainDotfileRequest,
    GetGroupDotfileRequest,
    GetUserDotfileRequest,
    UpdateBootstrapScriptRequest,
    UpdateDomainDotfileRequest,
    UpdateGroupDotfileRequest,
    UpdateUserDotfileRequest,
)

from .conftest import DomainDotfileFactory, GroupDotfileFactory, UserDotfileFactory


@pytest.mark.integration
class TestUserDotfileLifecycle:
    @pytest.mark.asyncio
    async def test_full_user_dotfile_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        """create → get → update → get → delete → verify 404"""
        unique = secrets.token_hex(4)
        path = f".lifecycle-{unique}"

        # Create
        await user_dotfile_factory(path=path, data="initial-data", permission="644")

        # Get
        get_result = await admin_registry.config.get_user_dotfile(GetUserDotfileRequest(path=path))
        assert get_result.path == path
        assert get_result.data == "initial-data"
        assert get_result.perm == "644"

        # Update
        await admin_registry.config.update_user_dotfile(
            UpdateUserDotfileRequest(path=path, data="updated-data", permission="755")
        )

        # Get (verify updated)
        get_after_update = await admin_registry.config.get_user_dotfile(
            GetUserDotfileRequest(path=path)
        )
        assert get_after_update.data == "updated-data"
        assert get_after_update.perm == "755"

        # Delete
        delete_result = await admin_registry.config.delete_user_dotfile(
            DeleteUserDotfileRequest(path=path)
        )
        assert delete_result.success is True

        # Verify 404
        with pytest.raises(NotFoundError):
            await admin_registry.config.get_user_dotfile(GetUserDotfileRequest(path=path))


@pytest.mark.integration
class TestBootstrapScriptLifecycle:
    @pytest.mark.asyncio
    async def test_bootstrap_script_update_and_retrieve(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """update → get → update again → get"""
        unique = secrets.token_hex(4)

        # First update
        script_v1 = f"#!/bin/bash\necho 'v1-{unique}'"
        await admin_registry.config.update_bootstrap_script(
            UpdateBootstrapScriptRequest(script=script_v1)
        )
        result_v1 = await admin_registry.config.get_bootstrap_script()
        assert result_v1.script == script_v1

        # Second update
        script_v2 = f"#!/bin/bash\necho 'v2-{unique}'\nexit 0"
        await admin_registry.config.update_bootstrap_script(
            UpdateBootstrapScriptRequest(script=script_v2)
        )
        result_v2 = await admin_registry.config.get_bootstrap_script()
        assert result_v2.script == script_v2

        # Cleanup: reset to empty
        await admin_registry.config.update_bootstrap_script(UpdateBootstrapScriptRequest(script=""))


@pytest.mark.integration
class TestGroupDotfileLifecycle:
    @pytest.mark.asyncio
    async def test_full_group_dotfile_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        group_dotfile_factory: GroupDotfileFactory,
    ) -> None:
        """create → get → update → delete → verify 404"""
        unique = secrets.token_hex(4)
        path = f".group-lifecycle-{unique}"
        group_id = str(group_fixture)

        # Create
        await group_dotfile_factory(path=path, data="group-initial", permission="644")

        # Get
        get_result = await admin_registry.config.get_group_dotfile(
            GetGroupDotfileRequest(group=group_id, path=path)
        )
        assert get_result.path == path
        assert get_result.data == "group-initial"

        # Update
        await admin_registry.config.update_group_dotfile(
            UpdateGroupDotfileRequest(
                group=group_id, path=path, data="group-updated", permission="755"
            )
        )
        get_after = await admin_registry.config.get_group_dotfile(
            GetGroupDotfileRequest(group=group_id, path=path)
        )
        assert get_after.data == "group-updated"
        assert get_after.perm == "755"

        # Delete
        delete_result = await admin_registry.config.delete_group_dotfile(
            DeleteGroupDotfileRequest(group=group_id, path=path)
        )
        assert delete_result.success is True

        # Verify 404
        with pytest.raises(NotFoundError):
            await admin_registry.config.get_group_dotfile(
                GetGroupDotfileRequest(group=group_id, path=path)
            )


@pytest.mark.integration
class TestDomainDotfileLifecycle:
    @pytest.mark.asyncio
    async def test_full_domain_dotfile_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        domain_dotfile_factory: DomainDotfileFactory,
    ) -> None:
        """create → get → update → delete → verify 404"""
        unique = secrets.token_hex(4)
        path = f".domain-lifecycle-{unique}"

        # Create
        await domain_dotfile_factory(path=path, data="domain-initial", permission="644")

        # Get
        get_result = await admin_registry.config.get_domain_dotfile(
            GetDomainDotfileRequest(domain=domain_fixture, path=path)
        )
        assert get_result.path == path
        assert get_result.data == "domain-initial"

        # Update
        await admin_registry.config.update_domain_dotfile(
            UpdateDomainDotfileRequest(
                domain=domain_fixture,
                path=path,
                data="domain-updated",
                permission="755",
            )
        )
        get_after = await admin_registry.config.get_domain_dotfile(
            GetDomainDotfileRequest(domain=domain_fixture, path=path)
        )
        assert get_after.data == "domain-updated"
        assert get_after.perm == "755"

        # Delete
        delete_result = await admin_registry.config.delete_domain_dotfile(
            DeleteDomainDotfileRequest(domain=domain_fixture, path=path)
        )
        assert delete_result.success is True

        # Verify 404
        with pytest.raises(NotFoundError):
            await admin_registry.config.get_domain_dotfile(
                GetDomainDotfileRequest(domain=domain_fixture, path=path)
            )
