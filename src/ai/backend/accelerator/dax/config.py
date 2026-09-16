import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

CONFIG_FILENAME: Final[str] = "dax-accelerator.toml"


class DAXPluginConfig(BaseModel):
    """The per-host `dax-accelerator.toml`, read once at plugin init."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_holders: int = Field(default=1, ge=1)
    allowlist: Sequence[str] | None = None
    allow_non_cxl: bool = False
    sysfs_root: Path = Path("/sys")
    dev_root: Path = Path("/dev")
    mock: bool = False
    path_on_host: Mapping[str, str] = Field(default_factory=dict)


def default_config_paths() -> list[Path]:
    """
    The lookup order for the config file.
    `BACKEND_CONFIG_FILE` is not consulted, since it names the agent's own TOML.
    """
    return [
        Path.cwd() / CONFIG_FILENAME,
        Path.home() / ".config" / "backend.ai" / CONFIG_FILENAME,
        Path("/etc/backend.ai") / CONFIG_FILENAME,
    ]


def load_config(config_paths: Sequence[Path]) -> tuple[DAXPluginConfig, Path | None]:
    """
    Read the first existing file among `config_paths`, or return the defaults.
    Raises `OSError`, `tomllib.TOMLDecodeError`, or `pydantic.ValidationError`.
    """
    for path in config_paths:
        if path.is_file():
            raw = tomllib.loads(path.read_text())
            return DAXPluginConfig.model_validate(raw), path
    return DAXPluginConfig(), None
