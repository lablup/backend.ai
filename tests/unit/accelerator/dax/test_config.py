from pathlib import Path

import pytest

from ai.backend.accelerator.dax.config import DAXPluginConfig, load_config
from ai.backend.common.types import SlotName

from .conftest import FakeSysfs, PluginFactory


class TestLoadConfig:
    @pytest.fixture
    def config_file(self, tmp_path: Path) -> Path:
        path = tmp_path / "dax-accelerator.toml"
        path.write_text(
            "max_holders = 2\n"
            'allowlist = ["dax-0x1a2b"]\n'
            "allow_non_cxl = true\n"
            'sysfs_root = "/fake/sys"\n'
            "mock = true\n"
            "[path_on_host]\n"
            '"dax0.0" = "/tmp/fake-dax0.0"\n'
        )
        return path

    def test_valid_file_is_parsed(self, config_file: Path, tmp_path: Path) -> None:
        config, path = load_config([tmp_path / "absent.toml", config_file])

        assert path == config_file
        assert config.max_holders == 2
        assert list(config.allowlist or []) == ["dax-0x1a2b"]
        assert config.allow_non_cxl is True
        assert config.sysfs_root == Path("/fake/sys")
        assert config.mock is True
        assert dict(config.path_on_host) == {"dax0.0": "/tmp/fake-dax0.0"}

    def test_missing_file_yields_defaults(self, tmp_path: Path) -> None:
        config, path = load_config([tmp_path / "absent.toml"])

        assert path is None
        assert config == DAXPluginConfig()


class TestPluginInvalidConfig:
    @pytest.fixture(autouse=True)
    def device(self, fake_sysfs: FakeSysfs) -> None:
        fake_sysfs.add_cxl_device("dax0.0")

    @pytest.mark.parametrize(
        "extra_toml",
        [
            pytest.param("max_holders = 0", id="max_holders-below-1"),
            pytest.param("unknown_key = 1", id="unknown-key"),
            pytest.param("max_holders = [", id="toml-syntax"),
        ],
    )
    async def test_invalid_config_admits_no_device(
        self,
        plugin_factory: PluginFactory,
        extra_toml: str,
    ) -> None:
        plugin = await plugin_factory(extra_toml)

        hwinfo = await plugin.get_node_hwinfo()
        assert list(await plugin.list_devices()) == []
        assert await plugin.available_slots() == {SlotName("dax.device"): 0}
        assert hwinfo["status"] == "unavailable"
        assert hwinfo["metadata"]["invalid_config"]
