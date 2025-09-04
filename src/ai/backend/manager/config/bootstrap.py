from pathlib import Path
from pprint import pformat
from typing import Any, Self

from pydantic import BaseModel, Field

from ai.backend.logging.config import LoggingConfig
from ai.backend.logging.types import LogLevel
from ai.backend.manager.config.unified import (
    DatabaseConfig,
    DebugConfig,
    EtcdConfig,
    ManagerConfig,
    PyroscopeConfig,
)

from .constant import MANAGER_LOCAL_CFG_OVERRIDE_ENVS
from .loader.config_overrider import ConfigOverrider
from .loader.env_loader import EnvLoader
from .loader.loader_chain import LoaderChain
from .loader.toml_loader import TomlConfigLoader


# TODO: Remove useless config fields from this
class BootstrapConfig(BaseModel):
    db: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="""
        Database configuration settings.
        Defines how the manager connects to its PostgreSQL database.
        Contains connection details, credentials, and pool settings.
        """,
    )
    etcd: EtcdConfig = Field(
        default_factory=EtcdConfig,
        description="""
        Etcd configuration settings.
        Used for distributed coordination between manager instances.
        Contains connection details and authentication information.
        """,
    )
    manager: ManagerConfig = Field(
        default_factory=ManagerConfig,
        description="""
        Core manager service configuration.
        Controls how the manager operates, communicates, and scales.
        Includes network settings, process management, and service parameters.
        """,
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="""
        Logging system configuration.
        Controls how logs are formatted, filtered, and stored.
        Detailed configuration is handled in ai.backend.logging.
        """,
    )
    pyroscope: PyroscopeConfig = Field(
        default_factory=PyroscopeConfig,
        description="""
        Pyroscope profiling configuration.
        Controls integration with the Pyroscope performance profiling tool.
        Used for monitoring and analyzing application performance.
        """,
    )
    debug: DebugConfig = Field(
        default_factory=DebugConfig,
        description="""
        Debugging options configuration.
        Controls various debugging features and tools.
        Should typically be disabled in production environments.
        """,
    )

    def __repr__(self):
        return pformat(self.model_dump())

    @classmethod
    async def load_from_file(cls, config_path: Path, log_level: LogLevel = LogLevel.NOTSET) -> Self:
        """
        Load configuration from a config file.

        All configurations are loaded by a single LoaderChain in config_provider_ctx.
        But BootstrapConfig must be loaded before config_provider_ctx is invoked since they are required for the manager boot process.
        """

        overrides: list[tuple[tuple[str, ...], Any]] = [
            (("debug", "enabled"), log_level == LogLevel.DEBUG),
        ]
        if log_level != LogLevel.NOTSET:
            overrides += [
                (("logging", "level"), log_level),
                (("logging", "pkg-ns", "ai.backend"), log_level),
            ]

        file_loader = TomlConfigLoader(config_path, "manager")
        env_loader = EnvLoader(MANAGER_LOCAL_CFG_OVERRIDE_ENVS)
        cfg_overrider = ConfigOverrider(overrides)
        cfg_loader = LoaderChain([
            file_loader,
            env_loader,
            cfg_overrider,
        ])
        raw_cfg = await cfg_loader.load()

        cfg = cls.model_validate(raw_cfg, by_name=True)
        return cfg
