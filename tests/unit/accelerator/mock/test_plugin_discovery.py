from dataclasses import dataclass
from importlib.metadata import EntryPoint

import pytest
from pytest_mock import MockerFixture

from ai.backend.accelerator.mock.plugin import MockPlugin
from ai.backend.agent.resources import AbstractComputePlugin, ComputePluginContext


@dataclass(frozen=True)
class _MockPluginDiscoveryCase:
    allowlist: set[str] | None
    expected_plugins: dict[str, type[AbstractComputePlugin]]


class TestMockPluginDiscovery:
    @pytest.fixture
    def scanned_mock_entrypoint(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "ai.backend.common.plugin.scan_entrypoints",
            return_value=[
                EntryPoint(
                    name="mock",
                    value="ai.backend.accelerator.mock.plugin:MockPlugin",
                    group=ComputePluginContext.plugin_group,
                )
            ],
        )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _MockPluginDiscoveryCase(allowlist=None, expected_plugins={}),
                id="skipped_without_an_allowlist",
            ),
            pytest.param(
                _MockPluginDiscoveryCase(
                    allowlist={"ai.backend.accelerator.mock"},
                    expected_plugins={"mock": MockPlugin},
                ),
                id="loaded_when_listed_in_the_allowlist",
            ),
        ],
    )
    @pytest.mark.usefixtures("scanned_mock_entrypoint")
    def test_discovered_plugins(self, case: _MockPluginDiscoveryCase) -> None:
        discovered = ComputePluginContext.discover_plugins(
            ComputePluginContext.plugin_group, allowlist=case.allowlist
        )

        assert dict(discovered) == case.expected_plugins
