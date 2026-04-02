from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import (
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
)
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.config import (
    CreateDomainDotfileRequest,
    CreateDotfileResponse,
    CreateGroupDotfileRequest,
    CreateUserDotfileRequest,
    DeleteDomainDotfileRequest,
    DeleteDotfileResponse,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
    GetBootstrapScriptResponse,
    GetDomainDotfileRequest,
    GetDotfileResponse,
    GetGroupDotfileRequest,
    GetUserDotfileRequest,
    ListDotfilesResponse,
    UpdateBootstrapScriptRequest,
    UpdateBootstrapScriptResponse,
    UpdateDomainDotfileRequest,
    UpdateDotfileResponse,
    UpdateGroupDotfileRequest,
    UpdateUserDotfileRequest,
)

from .conftest import DomainDotfileFactory, GroupDotfileFactory, UserDotfileFactory

# ---------------------------------------------------------------------------
# User Dotfile Tests
# ---------------------------------------------------------------------------


class TestUserDotfileCreate:
    async def test_admin_creates_user_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await user_dotfile_factory(
            path=f".bashrc-{unique}",
            data=f"export PATH=$PATH:/opt/{unique}",
            permission="755",
        )
        assert isinstance(result, CreateDotfileResponse)

    async def test_create_duplicate_user_dotfile_fails(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".dup-{unique}"
        await user_dotfile_factory(path=path, data="first", permission="644")
        with pytest.raises(InvalidRequestError):
            await admin_registry.config.create_user_dotfile(
                CreateUserDotfileRequest(path=path, data="second", permission="644")
            )

    async def test_regular_user_creates_own_dotfile(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".user-own-{unique}"
        result = await user_registry.config.create_user_dotfile(
            CreateUserDotfileRequest(path=path, data="user content", permission="644")
        )
        assert isinstance(result, CreateDotfileResponse)
        # Cleanup
        await user_registry.config.delete_user_dotfile(DeleteUserDotfileRequest(path=path))


class TestUserDotfileGet:
    async def test_admin_gets_user_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".get-{unique}"
        await user_dotfile_factory(path=path, data="get-test-data", permission="600")
        result = await admin_registry.config.get_user_dotfile(GetUserDotfileRequest(path=path))
        assert isinstance(result, GetDotfileResponse)
        assert result.path == path
        assert result.data == "get-test-data"
        assert result.perm == "600"

    async def test_admin_lists_user_dotfiles(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        unique1 = secrets.token_hex(4)
        unique2 = secrets.token_hex(4)
        await user_dotfile_factory(path=f".list-a-{unique1}", data="a", permission="644")
        await user_dotfile_factory(path=f".list-b-{unique2}", data="b", permission="644")
        result = await admin_registry.config.list_user_dotfiles()
        assert isinstance(result, ListDotfilesResponse)
        # List response is a plain array (via BaseRootResponseModel)
        paths = [item.path for item in result.root]
        assert f".list-a-{unique1}" in paths
        assert f".list-b-{unique2}" in paths

    async def test_list_user_dotfiles_returns_plain_array_json(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        """Verify the API returns a plain JSON array with 'permission' field.

        This is a regression test for BA-5420 to ensure the response format
        matches the legacy behavior (plain array with 'permission' field,
        not {"items": [...]} with 'perm' field).
        """
        unique = secrets.token_hex(4)
        path = f".list-test-{unique}"
        await user_dotfile_factory(path=path, data="test-data", permission="755")
        try:
            result = await admin_registry.config.list_user_dotfiles()
            # The response should be a plain array
            assert isinstance(result.root, list)
            # Verify model_dump returns the plain array (not wrapped)
            dumped = result.model_dump()
            assert isinstance(dumped, list)
            # Find the test item and verify it has 'permission' field
            test_items = [
                item for item in dumped if isinstance(item, dict) and item.get("path") == path
            ]
            assert len(test_items) == 1
            test_item = test_items[0]
            # Verify field name is 'permission' (not 'perm')
            assert "permission" in test_item
            assert test_item["permission"] == "755"
            # Verify no 'perm' field (should be renamed to 'permission')
            assert "perm" not in test_item
        finally:
            # Cleanup
            await admin_registry.config.delete_user_dotfile(DeleteUserDotfileRequest(path=path))

    async def test_get_nonexistent_user_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.config.get_user_dotfile(
                GetUserDotfileRequest(path=".nonexistent-dotfile")
            )


class TestUserDotfileUpdate:
    async def test_admin_updates_user_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".update-{unique}"
        await user_dotfile_factory(path=path, data="original", permission="644")
        update_result = await admin_registry.config.update_user_dotfile(
            UpdateUserDotfileRequest(path=path, data="updated-data", permission="755")
        )
        assert isinstance(update_result, UpdateDotfileResponse)
        # Verify the update
        get_result = await admin_registry.config.get_user_dotfile(GetUserDotfileRequest(path=path))
        assert get_result.data == "updated-data"
        assert get_result.perm == "755"

    async def test_update_nonexistent_user_dotfile_fails(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.config.update_user_dotfile(
                UpdateUserDotfileRequest(path=".nonexistent-update", data="data", permission="644")
            )


class TestUserDotfileDelete:
    async def test_admin_deletes_user_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        user_dotfile_factory: UserDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".delete-{unique}"
        await user_dotfile_factory(path=path, data="to-delete", permission="644")
        delete_result = await admin_registry.config.delete_user_dotfile(
            DeleteUserDotfileRequest(path=path)
        )
        assert isinstance(delete_result, DeleteDotfileResponse)
        assert delete_result.success is True
        # Verify gone
        with pytest.raises(NotFoundError):
            await admin_registry.config.get_user_dotfile(GetUserDotfileRequest(path=path))

    async def test_delete_nonexistent_user_dotfile_fails(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.config.delete_user_dotfile(
                DeleteUserDotfileRequest(path=".nonexistent-delete")
            )


# ---------------------------------------------------------------------------
# Bootstrap Script Tests
# ---------------------------------------------------------------------------


class TestBootstrapScript:
    async def test_get_bootstrap_script_default_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.config.get_bootstrap_script()
        assert isinstance(result, GetBootstrapScriptResponse)
        # Bootstrap script response is a plain string (via BaseRootResponseModel)
        assert result.root == ""

    async def test_update_and_get_bootstrap_script(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        unique = secrets.token_hex(4)
        script_content = f"#!/bin/bash\necho 'hello {unique}'"
        update_result = await admin_registry.config.update_bootstrap_script(
            UpdateBootstrapScriptRequest(script=script_content)
        )
        assert isinstance(update_result, UpdateBootstrapScriptResponse)
        get_result = await admin_registry.config.get_bootstrap_script()
        assert get_result.root == script_content
        # Reset to empty for cleanup
        await admin_registry.config.update_bootstrap_script(UpdateBootstrapScriptRequest(script=""))

    async def test_get_bootstrap_script_returns_plain_string_json(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Verify the API returns a plain JSON string, not wrapped in an object.

        This is a regression test for BA-5420 to ensure the response format
        matches the legacy behavior (plain string, not {"script": "..."}).
        """
        unique = secrets.token_hex(4)
        script_content = f"echo test-{unique}"
        await admin_registry.config.update_bootstrap_script(
            UpdateBootstrapScriptRequest(script=script_content)
        )
        try:
            result = await admin_registry.config.get_bootstrap_script()
            # The response should be a plain string
            assert result.root == script_content
            # Verify model_dump returns the plain string (not wrapped)
            dumped = result.model_dump()
            assert dumped == script_content
            assert isinstance(dumped, str)
        finally:
            # Cleanup
            await admin_registry.config.update_bootstrap_script(
                UpdateBootstrapScriptRequest(script="")
            )


# ---------------------------------------------------------------------------
# Group Dotfile Tests
# ---------------------------------------------------------------------------


class TestGroupDotfileCreate:
    async def test_admin_creates_group_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        group_dotfile_factory: GroupDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await group_dotfile_factory(
            path=f".group-rc-{unique}",
            data=f"# group config {unique}",
            permission="644",
        )
        assert isinstance(result, CreateDotfileResponse)

    async def test_regular_user_cannot_create_group_dotfile(
        self,
        user_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        unique = secrets.token_hex(4)
        with pytest.raises(PermissionDeniedError):
            await user_registry.config.create_group_dotfile(
                CreateGroupDotfileRequest(
                    group=str(group_fixture),
                    path=f".denied-{unique}",
                    data="denied",
                    permission="644",
                )
            )


class TestGroupDotfileGet:
    async def test_admin_gets_group_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        group_dotfile_factory: GroupDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".group-get-{unique}"
        await group_dotfile_factory(path=path, data="group-get-data", permission="600")
        result = await admin_registry.config.get_group_dotfile(
            GetGroupDotfileRequest(group=str(group_fixture), path=path)
        )
        assert isinstance(result, GetDotfileResponse)
        assert result.path == path
        assert result.data == "group-get-data"
        assert result.perm == "600"

    async def test_admin_lists_group_dotfiles(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        group_dotfile_factory: GroupDotfileFactory,
    ) -> None:
        unique1 = secrets.token_hex(4)
        unique2 = secrets.token_hex(4)
        await group_dotfile_factory(path=f".glist-a-{unique1}", data="a", permission="644")
        await group_dotfile_factory(path=f".glist-b-{unique2}", data="b", permission="644")
        result = await admin_registry.config.list_group_dotfiles(
            GetGroupDotfileRequest(group=str(group_fixture))
        )
        assert isinstance(result, ListDotfilesResponse)
        # List response is a plain array (via BaseRootResponseModel)
        paths = [item.path for item in result.root]
        assert f".glist-a-{unique1}" in paths
        assert f".glist-b-{unique2}" in paths

    async def test_list_group_dotfiles_returns_plain_array_json(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        group_dotfile_factory: GroupDotfileFactory,
    ) -> None:
        """Verify the API returns a plain JSON array with 'permission' field.

        This is a regression test for BA-5420 to ensure the response format
        matches the legacy behavior (plain array with 'permission' field,
        not {"items": [...]} with 'perm' field).
        """
        unique = secrets.token_hex(4)
        path = f".glist-test-{unique}"
        await group_dotfile_factory(path=path, data="test-data", permission="755")
        try:
            result = await admin_registry.config.list_group_dotfiles(
                GetGroupDotfileRequest(group=str(group_fixture))
            )
            # The response should be a plain array
            assert isinstance(result.root, list)
            # Verify model_dump returns the plain array (not wrapped)
            dumped = result.model_dump()
            assert isinstance(dumped, list)
            # Find the test item and verify it has 'permission' field
            test_items = [
                item for item in dumped if isinstance(item, dict) and item.get("path") == path
            ]
            assert len(test_items) == 1
            test_item = test_items[0]
            # Verify field name is 'permission' (not 'perm')
            assert "permission" in test_item
            assert test_item["permission"] == "755"
            # Verify no 'perm' field (should be renamed to 'permission')
            assert "perm" not in test_item
        finally:
            # Cleanup
            await admin_registry.config.delete_group_dotfile(
                DeleteGroupDotfileRequest(group=str(group_fixture), path=path)
            )


class TestGroupDotfileUpdate:
    async def test_admin_updates_group_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        group_dotfile_factory: GroupDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".group-upd-{unique}"
        await group_dotfile_factory(path=path, data="original-group", permission="644")
        update_result = await admin_registry.config.update_group_dotfile(
            UpdateGroupDotfileRequest(
                group=str(group_fixture),
                path=path,
                data="updated-group-data",
                permission="755",
            )
        )
        assert isinstance(update_result, UpdateDotfileResponse)
        get_result = await admin_registry.config.get_group_dotfile(
            GetGroupDotfileRequest(group=str(group_fixture), path=path)
        )
        assert get_result.data == "updated-group-data"
        assert get_result.perm == "755"


class TestGroupDotfileDelete:
    async def test_admin_deletes_group_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        group_dotfile_factory: GroupDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".group-del-{unique}"
        await group_dotfile_factory(path=path, data="to-delete", permission="644")
        delete_result = await admin_registry.config.delete_group_dotfile(
            DeleteGroupDotfileRequest(group=str(group_fixture), path=path)
        )
        assert isinstance(delete_result, DeleteDotfileResponse)
        assert delete_result.success is True
        with pytest.raises(NotFoundError):
            await admin_registry.config.get_group_dotfile(
                GetGroupDotfileRequest(group=str(group_fixture), path=path)
            )


# ---------------------------------------------------------------------------
# Domain Dotfile Tests
# ---------------------------------------------------------------------------


class TestDomainDotfileCreate:
    async def test_admin_creates_domain_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_dotfile_factory: DomainDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await domain_dotfile_factory(
            path=f".domain-rc-{unique}",
            data=f"# domain config {unique}",
            permission="644",
        )
        assert isinstance(result, CreateDotfileResponse)

    async def test_regular_user_cannot_create_domain_dotfile(
        self,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        with pytest.raises(PermissionDeniedError):
            await user_registry.config.create_domain_dotfile(
                CreateDomainDotfileRequest(
                    domain=domain_fixture,
                    path=f".denied-{unique}",
                    data="denied",
                    permission="644",
                )
            )


class TestDomainDotfileGet:
    async def test_admin_gets_domain_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        domain_dotfile_factory: DomainDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".domain-get-{unique}"
        await domain_dotfile_factory(path=path, data="domain-get-data", permission="600")
        result = await admin_registry.config.get_domain_dotfile(
            GetDomainDotfileRequest(domain=domain_fixture, path=path)
        )
        assert isinstance(result, GetDotfileResponse)
        assert result.path == path
        assert result.data == "domain-get-data"
        assert result.perm == "600"

    async def test_admin_lists_domain_dotfiles(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        domain_dotfile_factory: DomainDotfileFactory,
    ) -> None:
        unique1 = secrets.token_hex(4)
        unique2 = secrets.token_hex(4)
        await domain_dotfile_factory(path=f".dlist-a-{unique1}", data="a", permission="644")
        await domain_dotfile_factory(path=f".dlist-b-{unique2}", data="b", permission="644")
        result = await admin_registry.config.list_domain_dotfiles(
            GetDomainDotfileRequest(domain=domain_fixture)
        )
        assert isinstance(result, ListDotfilesResponse)
        # List response is a plain array (via BaseRootResponseModel)
        paths = [item.path for item in result.root]
        assert f".dlist-a-{unique1}" in paths
        assert f".dlist-b-{unique2}" in paths

    async def test_list_domain_dotfiles_returns_plain_array_json(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        domain_dotfile_factory: DomainDotfileFactory,
    ) -> None:
        """Verify the API returns a plain JSON array with 'permission' field.

        This is a regression test for BA-5420 to ensure the response format
        matches the legacy behavior (plain array with 'permission' field,
        not {"items": [...]} with 'perm' field).
        """
        unique = secrets.token_hex(4)
        path = f".dlist-test-{unique}"
        await domain_dotfile_factory(path=path, data="test-data", permission="755")
        try:
            result = await admin_registry.config.list_domain_dotfiles(
                GetDomainDotfileRequest(domain=domain_fixture)
            )
            # The response should be a plain array
            assert isinstance(result.root, list)
            # Verify model_dump returns the plain array (not wrapped)
            dumped = result.model_dump()
            assert isinstance(dumped, list)
            # Find the test item and verify it has 'permission' field
            test_items = [
                item for item in dumped if isinstance(item, dict) and item.get("path") == path
            ]
            assert len(test_items) == 1
            test_item = test_items[0]
            # Verify field name is 'permission' (not 'perm')
            assert "permission" in test_item
            assert test_item["permission"] == "755"
            # Verify no 'perm' field (should be renamed to 'permission')
            assert "perm" not in test_item
        finally:
            # Cleanup
            await admin_registry.config.delete_domain_dotfile(
                DeleteDomainDotfileRequest(domain=domain_fixture, path=path)
            )


class TestDomainDotfileUpdate:
    async def test_admin_updates_domain_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        domain_dotfile_factory: DomainDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".domain-upd-{unique}"
        await domain_dotfile_factory(path=path, data="original-domain", permission="644")
        update_result = await admin_registry.config.update_domain_dotfile(
            UpdateDomainDotfileRequest(
                domain=domain_fixture,
                path=path,
                data="updated-domain-data",
                permission="755",
            )
        )
        assert isinstance(update_result, UpdateDotfileResponse)
        get_result = await admin_registry.config.get_domain_dotfile(
            GetDomainDotfileRequest(domain=domain_fixture, path=path)
        )
        assert get_result.data == "updated-domain-data"
        assert get_result.perm == "755"


class TestDomainDotfileDelete:
    async def test_admin_deletes_domain_dotfile(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        domain_dotfile_factory: DomainDotfileFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        path = f".domain-del-{unique}"
        await domain_dotfile_factory(path=path, data="to-delete", permission="644")
        delete_result = await admin_registry.config.delete_domain_dotfile(
            DeleteDomainDotfileRequest(domain=domain_fixture, path=path)
        )
        assert isinstance(delete_result, DeleteDotfileResponse)
        assert delete_result.success is True
        with pytest.raises(NotFoundError):
            await admin_registry.config.get_domain_dotfile(
                GetDomainDotfileRequest(domain=domain_fixture, path=path)
            )
