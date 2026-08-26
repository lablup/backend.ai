from __future__ import annotations

import re
import shutil
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, Self, override

import pytest

from ai.backend.common.types import HostPortPair
from ai.backend.install.context import Context, current_log
from ai.backend.install.types import (
    DistInfo,
    HarborOptions,
    InstallInfo,
    InstallType,
    InstallVariable,
    OSInfo,
    Platform,
    ServerAddr,
    SftpAgentOptions,
)
from ai.backend.install.widgets import SetupLog


class RecordingLog(SetupLog):
    """Records progress output instead of rendering it.

    `SetupLog.write` scrolls the widget, which needs a running Textual app.
    """

    written: list[str]

    def __init__(self) -> None:
        super().__init__()
        self.written = []

    @override
    def write(self, data: object, scroll_end: bool | None = None, **kwargs: Any) -> Self:
        self.written.append(str(data))
        return self

    @override
    async def wait_continue(self) -> None:
        return None


class SedMiss(AssertionError):
    """A `sed_in_place` pattern matched nothing in the config template.

    `Context.sed_in_place` is a silent no-op on a miss, so a key renamed in
    `configs/**` would leave the installed config on its template default.
    """


class InstallerHarness(Context):
    """Runs the real `configure_*` steps against copies of the real templates.

    Everything that leaves the process (manager CLI, etcd, shell) is recorded
    rather than executed, so a step exercises its file handling alone.
    """

    base_path: Path
    manager_cli_calls: list[list[str]]
    appproxy_cli_calls: list[list[str]]
    etcd_writes: list[tuple[str, Any]]
    shell_scripts: list[str]
    exec_calls: list[list[str]]

    def __init__(self, base_path: Path, install_variable: InstallVariable) -> None:
        self.base_path = base_path
        self.manager_cli_calls = []
        self.appproxy_cli_calls = []
        self.etcd_writes = []
        self.shell_scripts = []
        self.exec_calls = []
        self._post_guides = []
        self.install_variable = install_variable
        self.log = current_log.get()
        self.cwd = base_path
        self.dist_info = DistInfo(target_path=base_path)
        self.os_info = OSInfo(
            platform=Platform.LINUX_X86_64, distro="Ubuntu", distro_variants=set()
        )
        self.docker_sudo = []
        self.non_interactive = True
        self.install_info = self.hydrate_install_info()

    @override
    def hydrate_install_info(self) -> InstallInfo:
        return self._build_install_info(
            install_type=InstallType.SOURCE,
            base_path=self.base_path,
            local_proxy_port=5050,
            loopback_aliases=("127.0.0.1", "localhost"),
            harbor=(
                HarborOptions(
                    hostname=self.install_variable.public_facing_address,
                    http_port=self.install_variable.harbor_http_port,
                    admin_password=self.install_variable.harbor_admin_password,
                )
                if self.install_variable.with_harbor
                else None
            ),
            sftp_agent=(
                SftpAgentOptions(
                    rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6013)),
                    watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6015)),
                    sock_port=6017,
                    ipc_base_path="ipc/agent-sftp",
                    var_base_path="var/agent-sftp",
                    scaling_group="upload",
                )
                if self.install_variable.with_sftp_agent
                else None
            ),
        )

    @override
    def copy_config(self, template_name: str) -> Path:
        with self.resource_path("ai.backend.install.configs", template_name) as src_path:
            dst_path = self.base_path / template_name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy(src_path, dst_path)
        return dst_path

    @override
    def mangle_pkgname(self, name: str, fat: bool = False) -> str:
        return f"backendai-{name}"

    @staticmethod
    def _matches(pattern: str | re.Pattern[str], content: str) -> bool:
        match pattern:
            case re.Pattern():
                return pattern.search(content) is not None
            case _:
                return pattern in content

    @override
    @staticmethod
    def sed_in_place(path: Path, pattern: str | re.Pattern[str], replacement: str) -> None:
        if not InstallerHarness._matches(pattern, path.read_text()):
            raise SedMiss(f"{path.name}: no match for {pattern!r}")
        Context.sed_in_place(path, pattern, replacement)

    @override
    @staticmethod
    def sed_in_place_multi(path: Path, subs: Sequence[tuple[str | re.Pattern[str], str]]) -> None:
        for pattern, replacement in subs:
            InstallerHarness.sed_in_place(path, pattern, replacement)

    @override
    async def run_manager_cli(self, cmdargs: Sequence[str]) -> None:
        self.manager_cli_calls.append(list(cmdargs))

    @override
    async def run_appproxy_coordinator_cli(self, cmdargs: Sequence[str]) -> None:
        self.appproxy_cli_calls.append(list(cmdargs))

    @override
    async def etcd_put_json(
        self, key: str, value: Any, *, max_retries: int = 30, retry_interval: float = 2.0
    ) -> None:
        self.etcd_writes.append((key, value))

    @override
    async def run_shell(self, script: str, **kwargs: Any) -> int:
        self.shell_scripts.append(script)
        return 0

    @override
    async def run_exec(self, cmdargs: Sequence[str], **kwargs: Any) -> int:
        self.exec_calls.append(list(cmdargs))
        return 0


@pytest.fixture
def install_variable() -> InstallVariable:
    return InstallVariable(public_facing_address="127.0.0.1")


@pytest.fixture
def harness(
    tmp_path: Path,
    install_variable: InstallVariable,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[InstallerHarness]:
    monkeypatch.chdir(tmp_path)
    token = current_log.set(RecordingLog())
    try:
        yield InstallerHarness(tmp_path, install_variable)
    finally:
        current_log.reset(token)
