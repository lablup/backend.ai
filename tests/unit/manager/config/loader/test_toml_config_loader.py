from pathlib import Path

from ai.backend.manager.config.loader.toml_loader import TomlConfigLoader

DUMMY_CFG = {"api": {"port": 8000}}
DUMMY_PATH = Path("/fake/config.toml")


async def test_toml_file_config_load(monkeypatch):
    def mock_read_from_file(path, daemon_name):
        assert path is None or path == DUMMY_PATH
        assert daemon_name == "manager"
        return DUMMY_CFG, Path("/resolved/config.toml")

    monkeypatch.setattr("ai.backend.common.config.read_from_file", mock_read_from_file)

    loader = TomlConfigLoader(DUMMY_PATH, daemon_name="manager")
    cfg = await loader.load()

    assert cfg == DUMMY_CFG
