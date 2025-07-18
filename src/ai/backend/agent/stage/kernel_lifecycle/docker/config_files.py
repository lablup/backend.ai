"""
Config files stage for kernel lifecycle.

This stage handles creation of environment and resource configuration files.
"""

import asyncio
import shutil
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Mapping, override

from ai.backend.agent.resources import ComputerContext, KernelResourceSpec
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import DeviceName


@dataclass
class ConfigFileSpec:
    config_dir: Path
    environ: Mapping[str, str]
    resource_spec: KernelResourceSpec
    computers: Mapping[DeviceName, ComputerContext]
    accelerator_envs: Mapping[str, str]  # Additional envs from accelerators


class ConfigFileSpecGenerator(ArgsSpecGenerator[ConfigFileSpec]):
    pass


@dataclass
class ConfigFileResult:
    environ_path: Path
    resource_path: Path
    environ_base_path: Path
    resource_base_path: Path


class ConfigFileProvisioner(Provisioner[ConfigFileSpec, ConfigFileResult]):
    """
    Provisioner for configuration file creation.

    Creates environ.txt and resource.txt files with environment variables
    and resource specifications.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-config-files"

    @override
    async def setup(self, spec: ConfigFileSpec) -> ConfigFileResult:
        await self._write_environ(spec)
        await self._write_resource_txt(spec)
        await self._write_backup_files(spec)

        return ConfigFileResult(
            environ_path=self._environ_path(spec),
            resource_path=self._resource_path(spec),
            environ_base_path=self._environ_base_path(spec),
            resource_base_path=self._resource_base_path(spec),
        )

    def _environ_path(self, spec: ConfigFileSpec) -> Path:
        return spec.config_dir / "environ.txt"

    def _environ_base_path(self, spec: ConfigFileSpec) -> Path:
        return spec.config_dir / "environ_base.txt"

    def _resource_path(self, spec: ConfigFileSpec) -> Path:
        return spec.config_dir / "resource.txt"

    def _resource_base_path(self, spec: ConfigFileSpec) -> Path:
        return spec.config_dir / "resource_base.txt"

    async def _write_environ(self, spec: ConfigFileSpec) -> None:
        loop = asyncio.get_running_loop()
        with StringIO() as buf:
            # Write basic environment variables
            for k, v in spec.environ.items():
                buf.write(f"{k}={v}\n")

            # Write accelerator environment variables
            for k, v in spec.accelerator_envs.items():
                buf.write(f"{k}={v}\n")

            await loop.run_in_executor(
                None,
                (self._environ_path(spec)).write_bytes,
                buf.getvalue().encode("utf8"),
            )

    async def _write_resource_txt(self, spec: ConfigFileSpec) -> None:
        loop = asyncio.get_running_loop()
        with StringIO() as buf:
            spec.resource_spec.write_to_file(buf)

            # Add device-specific resource data
            for dev_type, device_alloc in spec.resource_spec.allocations.items():
                if dev_type in spec.computers:
                    device_plugin = spec.computers[dev_type].instance
                    kvpairs = await device_plugin.generate_resource_data(device_alloc)
                    for k, v in kvpairs.items():
                        buf.write(f"{k}={v}\n")

            await loop.run_in_executor(
                None,
                (self._resource_path(spec)).write_bytes,
                buf.getvalue().encode("utf8"),
            )

    async def _write_backup_files(self, spec: ConfigFileSpec) -> None:
        # Create backup files for environ and resource
        environ_path = self._environ_path(spec)
        environ_base_path = self._environ_base_path(spec)
        resource_path = self._resource_path(spec)
        resource_base_path = self._resource_base_path(spec)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, shutil.copyfile, environ_path, environ_base_path)
        await loop.run_in_executor(None, shutil.copyfile, resource_path, resource_base_path)

    @override
    async def teardown(self, resource: ConfigFileResult) -> None:
        # Config files are cleaned up with scratch directory
        pass


class ConfigFileStage(ProvisionStage[ConfigFileSpec, ConfigFileResult]):
    """
    Stage for creating configuration files in kernel containers.
    """

    pass
