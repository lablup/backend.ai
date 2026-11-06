from pathlib import Path

import pytest

from ai.backend.manager.config.bootstrap import BootstrapConfig

_WHEELHOUSE_PATH = Path("/srv/wheelhouse")


@pytest.fixture
def config_file_allowing_the_wheelhouse(tmp_path: Path) -> Path:
    config_path = tmp_path / "manager.toml"
    config_path.write_text(f'[wheelhouse]\nallow = true\npath = "{_WHEELHOUSE_PATH}"\n')
    return config_path


async def test_load_from_file_reads_the_wheelhouse_section(
    config_file_allowing_the_wheelhouse: Path,
) -> None:
    bootstrap_config = await BootstrapConfig.load_from_file(config_file_allowing_the_wheelhouse)

    assert bootstrap_config.wheelhouse.allow is True
    assert bootstrap_config.wheelhouse.path == _WHEELHOUSE_PATH
