from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Self, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError, ConfigurationError
from ai.backend.common.plugins.base import PluginName
from ai.backend.common.types import AccessKey
from ai.backend.manager.config.unified import PluginsConfig
from ai.backend.manager.data.auth.types import UserData
from ai.backend.manager.dto.auth.lookup import UserLookupData
from ai.backend.manager.dto.auth.request import HTTPRequestData
from ai.backend.manager.errors.auth import InvalidUserLookupData
from ai.backend.manager.plugins.auth import AuthPlugin, AuthPluginConfig
from ai.backend.manager.plugins.loader import ManagerPluginLoader


class _Plugin(AuthPlugin):
    config: AuthPluginConfig

    def __init__(self, config: AuthPluginConfig) -> None:
        self.config = config

    @classmethod
    @override
    def create(cls, config: AuthPluginConfig) -> Self:
        return cls(config)

    @classmethod
    @override
    def name(cls) -> PluginName:
        return PluginName("sso")

    @classmethod
    @override
    def description(cls) -> str:
        return "An authentication plugin built for the tests."

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


class _OtherPlugin(_Plugin):
    @classmethod
    @override
    def name(cls) -> PluginName:
        return PluginName("ldap")


_PLUGIN_CLASSES: dict[str, type[AuthPlugin]] = {"sso": _Plugin, "ldap": _OtherPlugin}


def _entrypoints(*names: str) -> Any:
    def _scan(
        group_name: str,
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
    ) -> list[Any]:
        return [
            SimpleNamespace(name=name, load=lambda name=name: _PLUGIN_CLASSES[name])
            for name in names
            if name not in (blocklist or set())
        ]

    return _scan


def _make_loader(**auth_sections: dict[str, Any]) -> ManagerPluginLoader:
    return ManagerPluginLoader(PluginsConfig.model_validate({"auth": auth_sections}))


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
        assert list(UserLookupData.model_fields) == [
            "user_id",
            "email",
            "username",
            "access_key",
        ]


class TestAuthPlugin:
    @pytest.mark.parametrize(
        "method",
        [
            "create",
            "name",
            "description",
            "lookup_retry_count",
            "generate_lookup_data",
            "on_user_lookup_success",
            "on_user_lookup_error",
        ],
    )
    def test_every_contract_method_must_be_implemented(self, method: str) -> None:
        assert method in AuthPlugin.__abstractmethods__

    def test_carries_no_lifecycle_of_its_own(self) -> None:
        assert not hasattr(_Plugin, "init")
        assert not hasattr(_Plugin, "cleanup")

    def test_a_plugin_declares_its_own_retry_count(self) -> None:
        class _Patient(_Plugin):
            @classmethod
            @override
            def lookup_retry_count(cls) -> int:
                return 3

        assert _Patient.lookup_retry_count() == 3


class TestManagerPluginLoader:
    @pytest.fixture(autouse=True)
    def _patch_scan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._monkeypatch = monkeypatch

    def _install(self, *names: str) -> None:
        self._monkeypatch.setattr(
            "ai.backend.common.plugins.discovery.scan_entrypoints", _entrypoints(*names)
        )

    def test_loads_nothing_when_no_integration_is_installed(self) -> None:
        self._install()
        assert _make_loader().load().auth_plugin is None

    def test_loads_the_single_installed_plugin(self) -> None:
        self._install("sso")
        assert isinstance(_make_loader().load().auth_plugin, _Plugin)

    def test_builds_the_plugin_from_the_section_its_name_keys(self) -> None:
        self._install("sso")
        loader = _make_loader(sso={"issuer": "https://idp"}, ldap={"issuer": "https://other"})
        plugin = loader.load().auth_plugin
        assert isinstance(plugin, _Plugin)
        assert plugin.config.model_extra == {"issuer": "https://idp"}

    def test_builds_a_plugin_with_no_section_from_empty_settings(self) -> None:
        self._install("sso")
        plugin = _make_loader().load().auth_plugin
        assert isinstance(plugin, _Plugin)
        assert plugin.config.model_extra == {}

    def test_rejects_a_second_plugin_naming_every_candidate(self) -> None:
        self._install("sso", "ldap")
        with pytest.raises(ConfigurationError) as exc_info:
            _make_loader().load()
        message = str(exc_info.value)
        assert "ldap" in message
        assert "sso" in message
        assert "disabled-plugins" in message

    def test_passes_once_the_blocklist_leaves_one(self) -> None:
        self._install("sso", "ldap")
        loader = ManagerPluginLoader(PluginsConfig.model_validate({}), blocklist={"ldap"})
        assert isinstance(loader.load().auth_plugin, _Plugin)

    def test_skips_an_entry_point_that_is_not_an_auth_plugin(self) -> None:
        self._monkeypatch.setattr(
            "ai.backend.common.plugins.discovery.scan_entrypoints",
            lambda group_name, allowlist=None, blocklist=None: [
                SimpleNamespace(name="bogus", load=lambda: object)
            ],
        )
        assert _make_loader().load().auth_plugin is None
