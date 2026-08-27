from __future__ import annotations

from typing import Self, override

from ai.backend.common.plugins.base import BasePlugin, BasePluginConfig, PluginName


class _Config(BasePluginConfig):
    pass


class _DomainBase(BasePlugin[_Config]):
    pass


class _Concrete(_DomainBase):
    @classmethod
    @override
    def create(cls, config: _Config) -> Self:
        return cls()

    @classmethod
    @override
    def name(cls) -> PluginName:
        return PluginName("concrete")

    @classmethod
    @override
    def description(cls) -> str:
        return "A plugin built for the tests."


class TestBasePlugin:
    def test_requires_only_the_three_contract_methods(self) -> None:
        assert BasePlugin.__abstractmethods__ == frozenset({"create", "name", "description"})

    def test_a_domain_base_subclasses_it(self) -> None:
        assert issubclass(_DomainBase, BasePlugin)

    def test_a_plugin_subclasses_the_domain_base(self) -> None:
        plugin = _Concrete.create(_Config())
        assert plugin.name() == "concrete"
        assert plugin.description()

    def test_a_plugin_missing_a_contract_method_stays_abstract(self) -> None:
        class _Partial(_DomainBase):
            @classmethod
            @override
            def name(cls) -> PluginName:
                return PluginName("partial")

        assert _Partial.__abstractmethods__ == frozenset({"create", "description"})
