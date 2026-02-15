from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.config import ConfigClient
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

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_client(mock_session: MagicMock | None = None) -> BackendAIClient:
    return BackendAIClient(
        _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _ok_response(data: dict[str, object]) -> AsyncMock:
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value=data)
    return resp


class TestConfigClientUserDotfiles:
    @pytest.mark.asyncio
    async def test_create_user_dotfile(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = CreateUserDotfileRequest(
            path=".bashrc", data="alias ll='ls -la'", permission="644"
        )
        result = await config_client.create_user_dotfile(request)

        assert isinstance(result, CreateDotfileResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/user-config/dotfiles" in str(call_args[0][1])
        assert call_args.kwargs["json"]["path"] == ".bashrc"

    @pytest.mark.asyncio
    async def test_get_user_dotfile(self) -> None:
        mock_resp = _ok_response({"path": ".bashrc", "perm": "644", "data": "alias ll='ls -la'"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = GetUserDotfileRequest(path=".bashrc")
        result = await config_client.get_user_dotfile(request)

        assert isinstance(result, GetDotfileResponse)
        assert result.path == ".bashrc"
        assert result.perm == "644"
        assert result.data == "alias ll='ls -la'"

    @pytest.mark.asyncio
    async def test_list_user_dotfiles(self) -> None:
        mock_resp = _ok_response({
            "items": [
                {"path": ".bashrc", "perm": "644", "data": "content1"},
                {"path": ".vimrc", "perm": "644", "data": "content2"},
            ]
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        result = await config_client.list_user_dotfiles()

        assert isinstance(result, ListDotfilesResponse)
        assert len(result.items) == 2
        assert result.items[0].path == ".bashrc"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_update_user_dotfile(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = UpdateUserDotfileRequest(path=".bashrc", data="updated", permission="755")
        result = await config_client.update_user_dotfile(request)

        assert isinstance(result, UpdateDotfileResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"

    @pytest.mark.asyncio
    async def test_delete_user_dotfile(self) -> None:
        mock_resp = _ok_response({"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = DeleteUserDotfileRequest(path=".bashrc")
        result = await config_client.delete_user_dotfile(request)

        assert isinstance(result, DeleteDotfileResponse)
        assert result.success is True
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"


class TestConfigClientBootstrap:
    @pytest.mark.asyncio
    async def test_get_bootstrap_script(self) -> None:
        mock_resp = _ok_response({"script": "#!/bin/bash\necho hello"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        result = await config_client.get_bootstrap_script()

        assert isinstance(result, GetBootstrapScriptResponse)
        assert result.script == "#!/bin/bash\necho hello"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/user-config/bootstrap-script" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_update_bootstrap_script(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = UpdateBootstrapScriptRequest(script="#!/bin/bash\necho updated")
        result = await config_client.update_bootstrap_script(request)

        assert isinstance(result, UpdateBootstrapScriptResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args.kwargs["json"]["script"] == "#!/bin/bash\necho updated"


class TestConfigClientGroupDotfiles:
    @pytest.mark.asyncio
    async def test_create_group_dotfile(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = CreateGroupDotfileRequest(
            group="my-group", path=".bashrc", data="group content", permission="644"
        )
        result = await config_client.create_group_dotfile(request)

        assert isinstance(result, CreateDotfileResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/group-config/dotfiles" in str(call_args[0][1])
        assert call_args.kwargs["json"]["group"] == "my-group"

    @pytest.mark.asyncio
    async def test_get_group_dotfile(self) -> None:
        mock_resp = _ok_response({"path": ".bashrc", "perm": "644", "data": "group content"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = GetGroupDotfileRequest(group="my-group", path=".bashrc")
        result = await config_client.get_group_dotfile(request)

        assert isinstance(result, GetDotfileResponse)
        assert result.path == ".bashrc"

    @pytest.mark.asyncio
    async def test_list_group_dotfiles(self) -> None:
        mock_resp = _ok_response({"items": [{"path": ".bashrc", "perm": "644", "data": "content"}]})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = GetGroupDotfileRequest(group="my-group")
        result = await config_client.list_group_dotfiles(request)

        assert isinstance(result, ListDotfilesResponse)
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_update_group_dotfile(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = UpdateGroupDotfileRequest(
            group="my-group", path=".bashrc", data="updated", permission="755"
        )
        result = await config_client.update_group_dotfile(request)

        assert isinstance(result, UpdateDotfileResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"

    @pytest.mark.asyncio
    async def test_delete_group_dotfile(self) -> None:
        mock_resp = _ok_response({"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = DeleteGroupDotfileRequest(group="my-group", path=".bashrc")
        result = await config_client.delete_group_dotfile(request)

        assert isinstance(result, DeleteDotfileResponse)
        assert result.success is True


class TestConfigClientDomainDotfiles:
    @pytest.mark.asyncio
    async def test_create_domain_dotfile(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = CreateDomainDotfileRequest(
            domain="default", path=".bashrc", data="domain content", permission="644"
        )
        result = await config_client.create_domain_dotfile(request)

        assert isinstance(result, CreateDotfileResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/domain-config/dotfiles" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_domain_dotfile(self) -> None:
        mock_resp = _ok_response({"path": ".bashrc", "perm": "644", "data": "domain content"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = GetDomainDotfileRequest(domain="default", path=".bashrc")
        result = await config_client.get_domain_dotfile(request)

        assert isinstance(result, GetDotfileResponse)
        assert result.data == "domain content"

    @pytest.mark.asyncio
    async def test_list_domain_dotfiles(self) -> None:
        mock_resp = _ok_response({"items": [{"path": ".bashrc", "perm": "644", "data": "content"}]})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = GetDomainDotfileRequest(domain="default")
        result = await config_client.list_domain_dotfiles(request)

        assert isinstance(result, ListDotfilesResponse)
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_update_domain_dotfile(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = UpdateDomainDotfileRequest(
            domain="default", path=".bashrc", data="updated", permission="755"
        )
        result = await config_client.update_domain_dotfile(request)

        assert isinstance(result, UpdateDotfileResponse)

    @pytest.mark.asyncio
    async def test_delete_domain_dotfile(self) -> None:
        mock_resp = _ok_response({"success": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = DeleteDomainDotfileRequest(domain="default", path=".bashrc")
        result = await config_client.delete_domain_dotfile(request)

        assert isinstance(result, DeleteDotfileResponse)
        assert result.success is True
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"

    @pytest.mark.asyncio
    async def test_create_group_dotfile_with_domain(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = CreateGroupDotfileRequest(
            group="my-group",
            domain="default",
            path=".bashrc",
            data="content",
            permission="644",
        )
        result = await config_client.create_group_dotfile(request)

        assert isinstance(result, CreateDotfileResponse)
        call_args = mock_session.request.call_args
        assert call_args.kwargs["json"]["domain"] == "default"

    @pytest.mark.asyncio
    async def test_create_user_dotfile_with_owner_access_key(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        config_client = ConfigClient(client)

        request = CreateUserDotfileRequest(
            path=".bashrc",
            data="content",
            permission="644",
            owner_access_key="AKIAIOSFODNN7EXAMPLE",
        )
        result = await config_client.create_user_dotfile(request)

        assert isinstance(result, CreateDotfileResponse)
        call_args = mock_session.request.call_args
        assert call_args.kwargs["json"]["owner_access_key"] == "AKIAIOSFODNN7EXAMPLE"
