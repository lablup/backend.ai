from __future__ import annotations

import asyncio
import enum
from contextvars import ContextVar
from pathlib import Path

from rich.text import Text
from textual.app import App
from textual.containers import Vertical
from textual.widgets import Label, ProgressBar, RichLog, Static

from .common import detect_os
from .dev import (
    bootstrap_pants,
    install_editable_webui,
    install_git_hooks,
    install_git_lfs,
    pants_export,
)
from .docker import check_docker, check_docker_desktop_mount, get_preferred_pants_local_exec_root
from .http import wget
from .python import check_python
from .types import DistInfo, OSInfo, PackageSource

current_log: ContextVar[RichLog] = ContextVar("current_log")


class PostGuide(enum.Enum):
    UPDATE_ETC_HOSTS = 10


class Context:
    os_info: OSInfo

    _post_guides: list[PostGuide]

    def __init__(self, dist_info: DistInfo, app: App) -> None:
        self._post_guides = []
        self.app = app
        self.log = current_log.get()
        self.cwd = Path.cwd()
        self.dist_info = dist_info
        self.wget_sema = asyncio.Semaphore(3)

    def add_post_guide(self, guide: PostGuide) -> None:
        self._post_guides.append(guide)

    def show_post_guide(self) -> None:
        pass

    def log_header(self, title: str) -> None:
        self.log.write(Text.from_markup(f"[bright_green]{title}"))

    async def install_system_package(self, name: dict[str, list[str]]) -> None:
        distro_pkg_name = " ".join(name[self.os_info.distro])
        match self.os_info.distro:
            case "Debian":
                await self.run_shell(f"sudo apt-get install -y {distro_pkg_name}")
            case "RedHat":
                await self.run_shell(f"sudo yum install -y {distro_pkg_name}")
            case "SUSE":
                await self.run_shell(f"sudo zypper install -y {distro_pkg_name}")
            case "Darwin":
                await self.run_shell(f"brew install -y {distro_pkg_name}")

    async def run_shell(self, script: str, **kwargs) -> int:
        p = await asyncio.create_subprocess_shell(
            script,
            stdout=kwargs.pop("stdout", asyncio.subprocess.PIPE),
            stderr=kwargs.pop("stderr", asyncio.subprocess.PIPE),
            **kwargs,
        )

        async def read_stdout(stream: asyncio.StreamReader | None) -> None:
            if stream is None:
                return
            while True:
                line = await stream.readline()
                if not line:
                    break
                self.log.write(Text.from_ansi(line.decode()))

        async def read_stderr(stream: asyncio.StreamReader | None) -> None:
            if stream is None:
                return
            while True:
                line = await stream.readline()
                if not line:
                    break
                self.log.write(Text.from_ansi(line.decode(), style="bright_red"))

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(read_stdout(p.stdout))
                tg.create_task(read_stderr(p.stderr))
                exit_code = await p.wait()
        except asyncio.CancelledError:
            p.terminate()
            try:
                exit_code = await p.wait()
            except asyncio.TimeoutError:
                p.kill()
                exit_code = await p.wait()
        return exit_code

    async def install_halfstack(self, ha_setup: bool) -> None:
        pass

    async def load_fixtures(self) -> None:
        pass

    async def configure_manager(self) -> None:
        pass

    async def configure_agent(self) -> None:
        pass

    async def configure_storage_proxy(self) -> None:
        pass

    async def configure_webserver(self) -> None:
        pass

    async def configure_webui(self) -> None:
        pass

    async def dump_etcd_config(self) -> None:
        pass

    async def populate_images(self) -> None:
        pass


class DevContext(Context):
    async def check_prerequisites(self) -> None:
        self.os_info = await detect_os(self)
        await install_git_lfs(self)
        await install_git_hooks(self)
        await check_python(self)
        await check_docker(self)
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount(self)
        local_execution_root_dir = await get_preferred_pants_local_exec_root(self)
        await bootstrap_pants(self, local_execution_root_dir)

    async def install(self) -> None:
        await pants_export(self)
        await install_editable_webui(self)

    async def configure(self) -> None:
        await self.configure_manager()
        await self.configure_agent()
        await self.configure_storage_proxy()
        await self.configure_webserver()
        await self.configure_webui()

    async def populate_images(self) -> None:
        # TODO: docker pull
        pass


class PackageContext(Context):
    async def check_prerequisites(self) -> None:
        self.os_info = await detect_os(self)
        await check_docker(self)
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount(self)

    def _mangle_pkgname(self, name: str, fat: bool = False) -> str:
        if fat:
            return f"backendai-{name}-fat-{self.os_info.platform}"
        return f"backendai-{name}-{self.os_info.platform}"

    async def _validate_checksum(self, csum_path: Path) -> bool:
        proc = await asyncio.create_subprocess_exec(
            *["sha256sum", "-c", str(csum_path)],
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        exit_code = await proc.wait()
        if exit_code == 0:
            return True
        return False

    async def _fetch_package(self, name: str, vpane: Vertical) -> None:
        pkg_name = self._mangle_pkgname(name)
        pkg_path = self.dist_info.target_path / pkg_name
        csum_path = pkg_path.with_name(pkg_name + ".sha256")
        pkg_url = f"https://github.com/lablup/backend.ai/releases/download/{self.dist_info.version}/{pkg_name}"
        csum_url = pkg_url + ".sha256"
        self.log.write(f"Downloading {pkg_url}...")
        item = Static(classes="progress-item")
        label = Label(pkg_name, classes="progress-name")
        progress = ProgressBar(classes="progress-download")
        await item.mount(label)
        await item.mount(progress)
        await vpane.mount(item)
        async with self.wget_sema:
            try:
                await wget(pkg_url, pkg_path, progress)
            finally:
                item.remove()
        self.log.write(f"Verifying {pkg_url}...")
        await wget(csum_url, csum_path)
        if not await self._validate_checksum(csum_path):
            raise RuntimeError(
                "Failed to validate the checksum of {pkg_path}. "
                "Please check the install media and retry after removing it."
            )

    async def _verify_package(self, name: str, *, fat: bool) -> None:
        pkg_name = self._mangle_pkgname(name, fat=fat)
        pkg_path = self.dist_info.package_dir / pkg_name
        self.log.write(f"Verifying {pkg_path} ...")
        csum_path = pkg_path.with_name(pkg_name + ".sha256")
        if not await self._validate_checksum(csum_path):
            raise RuntimeError(
                "Failed to validate the checksum of {pkg_path}. "
                "Please check the install media and retry after removing it."
            )

    async def install(self) -> None:
        match self.dist_info.package_source:
            case PackageSource.GITHUB_RELEASE:
                # download (NOTE: we always use the lazy version here)
                self.log_header(
                    f"Downloading prebuilt packages into {self.dist_info.target_path}..."
                )
                vpane = Vertical(id="download-status")
                self.log.mount(vpane)
                try:
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self._fetch_package("manager", vpane))
                        tg.create_task(self._fetch_package("agent", vpane))
                        tg.create_task(self._fetch_package("agent-watcher", vpane))
                        # replace above with self._fetch_package("watcher", vpane)
                        tg.create_task(self._fetch_package("webserver", vpane))
                        tg.create_task(self._fetch_package("storage-proxy", vpane))
                        tg.create_task(self._fetch_package("client", vpane))
                        # TODO: tg.create_task(self._fetch_package("static wsproxy"))
                finally:
                    vpane.remove()
            case PackageSource.LOCAL_DIR:
                # use the local files
                await self._verify_package("manager", fat=self.dist_info.use_fat_binary)
                await self._verify_package("agent", fat=self.dist_info.use_fat_binary)
                await self._verify_package("agent-watcher", fat=self.dist_info.use_fat_binary)
                # replace above with await self._verify_package("watcher", fat=self.dist_info.use_fat_binary)
                await self._verify_package("webserver", fat=self.dist_info.use_fat_binary)
                await self._verify_package("storage-proxy", fat=self.dist_info.use_fat_binary)
                await self._verify_package("client", fat=self.dist_info.use_fat_binary)

    async def configure(self) -> None:
        await self.configure_manager()
        await self.configure_agent()
        await self.configure_storage_proxy()
        await self.configure_webserver()
        await self.configure_webui()
        # TODO: install as systemd services?

    async def populate_images(self) -> None:
        # TODO: docker load
        pass
