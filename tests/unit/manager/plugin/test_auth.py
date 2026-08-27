from __future__ import annotations

import dataclasses
from types import SimpleNamespace
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError, ConfigurationError
from ai.backend.common.plugin import AbstractPlugin
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.auth.lookup import UserLookupData
from ai.backend.manager.data.auth.request import HTTPRequestData
from ai.backend.manager.data.auth.types import UserData
from ai.backend.manager.errors.auth import InvalidUserLookupData
from ai.backend.manager.plugin.auth import AbstractAuthPlugin, AuthPluginContext


class _Plugin(AbstractAuthPlugin):
    @classmethod
    @override
    def lookup_retry_count(cls) -> int:
        return 1

    @override
    async def generate_lookup_data(self, request: HTTPRequestData) -> UserLookupData | None:
        return None

    @override
    async def on_user_lookup_success(self, user: UserData) -> None:
        pass

    @override
    async def on_user_lookup_error(self, error: BackendAIError) -> None:
        pass


def _entrypoints(*names: str) -> Any:
    def _scan(
        plugin_group: str,
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
    ) -> list[Any]:
        return [SimpleNamespace(name=name, load=lambda: _Plugin) for name in names]

    return _scan


class TestUserLookupData:
    @pytest.mark.parametrize(
        "lookup",
        [
            UserLookupData(user_id=UserID(UUID(int=1))),
            UserLookupData(email="a@b.c"),
            UserLookupData(username="alice"),
            UserLookupData(access_key=AccessKey("AK")),
        ],
    )
    def test_any_single_field_names_an_account(self, lookup: UserLookupData) -> None:
        assert any((lookup.user_id, lookup.email, lookup.username, lookup.access_key))

    def test_rejects_lookup_data_naming_no_account(self) -> None:
        with pytest.raises(InvalidUserLookupData):
            UserLookupData()

    def test_declares_the_fields_in_resolution_order(self) -> None:
        assert [f.name for f in dataclasses.fields(UserLookupData)] == [
            "user_id",
            "email",
            "username",
            "access_key",
        ]


class TestAbstractAuthPlugin:
    def test_concrete_plugin_needs_only_the_auth_methods(self) -> None:
        plugin = _Plugin({}, {})
        assert isinstance(plugin, AbstractPlugin)

    @pytest.mark.parametrize(
        "method",
        [
            "lookup_retry_count",
            "generate_lookup_data",
            "on_user_lookup_success",
            "on_user_lookup_error",
        ],
    )
    def test_every_auth_method_must_be_implemented(self, method: str) -> None:
        assert method in AbstractAuthPlugin.__abstractmethods__

    def test_a_plugin_declares_its_own_retry_count(self) -> None:
        class _Patient(_Plugin):
            @classmethod
            @override
            def lookup_retry_count(cls) -> int:
                return 3

        assert _Patient.lookup_retry_count() == 3

    async def test_lifecycle_defaults_are_no_ops(self) -> None:
        plugin = _Plugin({}, {})
        await plugin.init()
        await plugin.update_plugin_config({"secret": "s"})
        await plugin.cleanup()
        assert plugin.plugin_config == {"secret": "s"}


class TestAuthPluginContext:
    @pytest.fixture(autouse=True)
    def _patch_scan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._monkeypatch = monkeypatch

    def _discover(self, *names: str) -> list[tuple[str, type[AbstractAuthPlugin]]]:
        self._monkeypatch.setattr("ai.backend.common.plugin.scan_entrypoints", _entrypoints(*names))
        return list(AuthPluginContext.discover_plugins(AuthPluginContext.plugin_group))

    def test_loads_nothing_when_no_integration_is_installed(self) -> None:
        assert self._discover() == []

    def test_loads_the_single_installed_plugin(self) -> None:
        assert [name for name, _ in self._discover("sso")] == ["sso"]

    def test_rejects_a_second_plugin_naming_every_candidate(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            self._discover("sso", "ldap")
        message = str(exc_info.value)
        assert "ldap" in message
        assert "sso" in message
        assert "disabled-plugins" in message

    def test_passes_once_the_blocklist_leaves_one(self) -> None:
        self._monkeypatch.setattr(
            "ai.backend.common.plugin.scan_entrypoints",
            lambda group, allowlist=None, blocklist=None: [
                SimpleNamespace(name=name, load=lambda: _Plugin)
                for name in ("sso", "ldap")
                if name not in (blocklist or set())
            ],
        )
        ctx_plugins = list(
            AuthPluginContext.discover_plugins(AuthPluginContext.plugin_group, blocklist={"ldap"})
        )
        assert [name for name, _ in ctx_plugins] == ["sso"]

    def test_plugin_property_is_none_without_a_loaded_plugin(self) -> None:
        ctx = AuthPluginContext(SimpleNamespace(), {})  # type: ignore[arg-type]
        assert ctx.plugin is None

    def test_plugin_property_returns_the_loaded_plugin(self) -> None:
        ctx = AuthPluginContext(SimpleNamespace(), {})  # type: ignore[arg-type]
        plugin = _Plugin({}, {})
        ctx.plugins["sso"] = plugin
        assert ctx.plugin is plugin
