import asyncio
import json
import os
import stat
from collections.abc import Sequence
from http import HTTPStatus
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.accelerator.dax.plugin import HOLDER_SCAN_TIMEOUT, DAXPlugin
from ai.backend.common.docker import LabelName

ALIGN = 2 * 1024 * 1024
DEVICE_SIZE = 64 * ALIGN
FAKE_GID = 1234


class FakeSysfs:
    """Builds a sysfs tree with relative symlinks, shaped like the kernel's CXL/DAX layout."""

    root: Path
    _next_port: int

    def __init__(self, root: Path) -> None:
        self.root = root
        self._next_port = 2
        for sub in ("bus/cxl/devices", "bus/dax/devices", "bus/dax/drivers/device_dax"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        (root / "bus/dax/drivers/dax_hmem").mkdir(parents=True, exist_ok=True)

    def _link(self, link: Path, target: Path) -> None:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(os.path.relpath(target, link.parent))

    def _cxl_region(self, region: str, serials: Sequence[str]) -> Path:
        region_dir = self.root / "devices/platform/ACPI0017:00/root0/decoder0.0" / region
        if region_dir.exists():
            return region_dir
        region_dir.mkdir(parents=True)
        self._link(region_dir / "subsystem", self.root / "bus/cxl")
        for idx, serial in enumerate(serials):
            port = self._next_port
            self._next_port += 1
            endpoint_dir = self.root / f"devices/platform/ACPI0017:00/root0/port1/endpoint{port}"
            decoder_dir = endpoint_dir / f"decoder{port}.0"
            decoder_dir.mkdir(parents=True)
            memdev_dir = self.root / f"devices/pci0000:00/0000:00:0{port}.0/mem{port}"
            memdev_dir.mkdir(parents=True)
            (memdev_dir / "serial").write_text(f"{serial}\n")
            self._link(endpoint_dir / "uport", memdev_dir)
            self._link(self.root / f"bus/cxl/devices/decoder{port}.0", decoder_dir)
            (region_dir / f"target{idx}").write_text(f"decoder{port}.0\n")
        return region_dir

    def _dax_device(
        self,
        region_dir: Path,
        name: str,
        *,
        size: int,
        align: int,
        numa_node: int,
        target_node: int,
        driver: str | None,
    ) -> None:
        device_dir = region_dir / f"dax_{region_dir.name}" / name
        device_dir.mkdir(parents=True)
        for attr, value in (
            ("size", size),
            ("align", align),
            ("numa_node", numa_node),
            ("target_node", target_node),
        ):
            (device_dir / attr).write_text(f"{value}\n")
        if driver is not None:
            self._link(device_dir / "driver", self.root / "bus/dax/drivers" / driver)
        self._link(self.root / "bus/dax/devices" / name, device_dir)

    def add_cxl_device(
        self,
        name: str,
        *,
        region: str = "region0",
        serials: Sequence[str] = ("0x1a2b",),
        size: int = DEVICE_SIZE,
        align: int = ALIGN,
        numa_node: int = 1,
        target_node: int = 2,
        driver: str | None = "device_dax",
    ) -> None:
        region_dir = self._cxl_region(region, serials)
        self._dax_device(
            region_dir,
            name,
            size=size,
            align=align,
            numa_node=numa_node,
            target_node=target_node,
            driver=driver,
        )

    def add_non_cxl_device(
        self,
        name: str,
        *,
        region: str = "hmem0",
        size: int = DEVICE_SIZE,
        align: int = ALIGN,
    ) -> None:
        region_dir = self.root / "devices/platform" / region
        region_dir.mkdir(parents=True, exist_ok=True)
        self._dax_device(
            region_dir,
            name,
            size=size,
            align=align,
            numa_node=-1,
            target_node=0,
            driver="device_dax",
        )


class FakeStat:
    """A `stat_func` that reports every device node as a group-rw char device."""

    missing: set[str]
    modes: dict[str, int]

    def __init__(self) -> None:
        self.missing = set()
        self.modes = {}

    def __call__(self, path: Path) -> os.stat_result:
        if path.name in self.missing:
            raise FileNotFoundError(str(path))
        mode = self.modes.get(path.name, stat.S_IFCHR | 0o660)
        return os.stat_result((mode, 0, 0, 1, 0, FAKE_GID, 0, 0, 0, 0))


class FakeDocker:
    """A Docker daemon stand-in serving `containers.list(filters=...)` and `container.show()`."""

    inspects: dict[str, dict[str, Any]]
    list_error: Exception | None
    list_delay: float
    inspect_errors: dict[str, Exception]

    def __init__(self) -> None:
        self.inspects = {}
        self.list_error = None
        self.list_delay = 0.0
        self.inspect_errors = {}

    def add_container(
        self,
        container_id: str,
        *,
        kernel_id: str | None = None,
        devices: Sequence[str] | None = (),
        running: bool = True,
    ) -> None:
        labels = {LabelName.KERNEL_ID: kernel_id} if kernel_id is not None else {}
        self.inspects[container_id] = {
            "Id": container_id,
            "Config": {"Labels": labels},
            "State": {"Status": "running" if running else "exited", "Running": running},
            "HostConfig": {
                "Devices": (
                    [
                        {"PathOnHost": path, "PathInContainer": path, "CgroupPermissions": "rw"}
                        for path in devices
                    ]
                    if devices is not None
                    else None
                ),
            },
        }

    def remove_before_inspect(self, container_id: str) -> None:
        self.inspect_errors[container_id] = DockerError(
            HTTPStatus.NOT_FOUND, f"No such container: {container_id}"
        )

    def _matches(self, inspect: dict[str, Any], filters: dict[str, list[str]]) -> bool:
        labels = inspect["Config"]["Labels"]
        if any(label not in labels for label in filters.get("label", [])):
            return False
        statuses = filters.get("status")
        return statuses is None or inspect["State"]["Status"] in statuses

    async def _list(self, **kwargs: Any) -> list[MagicMock]:
        await asyncio.sleep(self.list_delay)
        if self.list_error is not None:
            raise self.list_error
        filters = json.loads(kwargs.get("filters", "{}"))
        return [
            self._container(container_id)
            for container_id, inspect in self.inspects.items()
            if self._matches(inspect, filters)
        ]

    def _container(self, container_id: str) -> MagicMock:
        async def show(**kwargs: Any) -> dict[str, Any]:
            error = self.inspect_errors.get(container_id)
            if error is not None:
                raise error
            return self.inspects[container_id]

        container = MagicMock()
        container.show = AsyncMock(side_effect=show)
        return container

    def __call__(self) -> MagicMock:
        docker = MagicMock()
        docker.containers.list = AsyncMock(side_effect=self._list)
        docker.close = AsyncMock()
        return docker


class PluginFactory:
    """Writes `dax-accelerator.toml` pointing at the fake sysfs and initializes a plugin."""

    sysfs: FakeSysfs
    stat_func: FakeStat
    config_path: Path
    docker: FakeDocker

    def __init__(
        self, sysfs: FakeSysfs, stat_func: FakeStat, config_path: Path, docker: FakeDocker
    ) -> None:
        self.sysfs = sysfs
        self.stat_func = stat_func
        self.config_path = config_path
        self.docker = docker

    async def __call__(
        self, extra_toml: str = "", *, holder_scan_timeout: float = HOLDER_SCAN_TIMEOUT
    ) -> DAXPlugin:
        self.config_path.write_text(
            f'sysfs_root = "{self.sysfs.root}"\ndev_root = "/host/dev"\n{extra_toml}\n'
        )
        plugin = DAXPlugin(
            {},
            {},
            config_paths=[self.config_path],
            stat_func=self.stat_func,
            docker_factory=self.docker,
            holder_scan_timeout=holder_scan_timeout,
        )
        await plugin.init()
        return plugin


@pytest.fixture
def fake_sysfs(tmp_path: Path) -> FakeSysfs:
    return FakeSysfs(tmp_path / "sys")


@pytest.fixture
def fake_stat() -> FakeStat:
    return FakeStat()


@pytest.fixture
def fake_docker() -> FakeDocker:
    return FakeDocker()


@pytest.fixture
def plugin_factory(
    fake_sysfs: FakeSysfs, fake_stat: FakeStat, fake_docker: FakeDocker, tmp_path: Path
) -> PluginFactory:
    return PluginFactory(fake_sysfs, fake_stat, tmp_path / "dax-accelerator.toml", fake_docker)
