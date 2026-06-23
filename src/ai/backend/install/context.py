from __future__ import annotations

import asyncio
import enum
import hashlib
import importlib.resources
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import uuid
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager as actxmgr
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

import aiofiles
import aiotools
import asyncpg
import tomlkit
from dateutil.tz import tzutc
from etcd_client import GRPCStatusError
from rich.text import Text
from ruamel.yaml import YAML
from textual.app import App
from textual.containers import Vertical
from textual.widgets import ProgressBar

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import HostPortPair

from .common import detect_os
from .dev import (
    bootstrap_pants,
    install_editable_webui,
    install_git_hooks,
    install_git_lfs,
    pants_export,
)
from .docker import (
    check_docker,
    check_docker_desktop_mount,
    determine_docker_sudo,
    get_preferred_pants_local_exec_root,
)
from .http import wget
from .python import check_python
from .types import (
    Accelerator,
    DistInfo,
    FrontendMode,
    HalfstackConfig,
    ImageSource,
    InstallInfo,
    InstallType,
    InstallVariable,
    OSInfo,
    PackageSource,
    Platform,
    PrerequisiteError,
    ServerAddr,
    ServiceConfig,
)
from .widgets import ProgressItem, SetupLog

current_log: ContextVar[SetupLog] = ContextVar("current_log")


class PostGuide(enum.Enum):
    UPDATE_ETC_HOSTS = 10


class Context(metaclass=ABCMeta):
    os_info: OSInfo
    docker_sudo: list[str]
    install_variable: InstallVariable

    _post_guides: list[PostGuide]

    def __init__(
        self,
        dist_info: DistInfo,
        install_variable: InstallVariable,
        app: App[None],
        *,
        non_interactive: bool = False,
    ) -> None:
        self._post_guides = []
        self.app = app
        self.install_variable = install_variable
        self.log = current_log.get()
        self.cwd = Path.cwd()
        self.dist_info = dist_info
        self.wget_sema = asyncio.Semaphore(3)
        self.non_interactive = non_interactive
        self.install_info = self.hydrate_install_info()

    @abstractmethod
    def hydrate_install_info(self) -> InstallInfo:
        raise NotImplementedError

    @abstractmethod
    async def _configure_mock_accelerator(self, accelerator: Accelerator) -> None:
        raise NotImplementedError

    def add_post_guide(self, guide: PostGuide) -> None:
        self._post_guides.append(guide)

    def show_post_guide(self) -> None:
        pass

    def log_header(self, title: str) -> None:
        self.log.write(Text.from_markup(f"[bright_green]:green_circle: {title}"))

    def mangle_pkgname(self, name: str, fat: bool = False) -> str:
        return f"backendai-{name}-{self.os_info.platform}"

    @staticmethod
    @contextmanager
    def resource_path(pkg: str, filename: str) -> Iterator[Path]:
        # pkg_resources is deprecated since .
        # importlib handles zipped resources as well.
        path_provider = importlib.resources.as_file(
            importlib.resources.files(pkg).joinpath(filename)
        )
        with path_provider as resource_path:
            yield resource_path

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
                await self.run_shell(f"brew install {distro_pkg_name}")

    async def run_exec(self, cmdargs: Sequence[str], **kwargs: Any) -> int:
        p = await asyncio.create_subprocess_exec(
            *cmdargs,
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
                exit_code = await asyncio.wait_for(p.wait(), timeout=5.0)
            except TimeoutError:
                p.kill()
                exit_code = await p.wait()
        return exit_code

    async def run_shell(self, script: str, **kwargs: Any) -> int:
        return await self.run_exec(["sh", "-c", script], **kwargs)

    def copy_config(self, template_name: str) -> Path:
        raise NotImplementedError

    @staticmethod
    def sed_in_place(path: Path, pattern: str | re.Pattern[str], replacement: str) -> None:
        content = path.read_text()
        match pattern:
            case str():
                content = content.replace(pattern, replacement)
            case re.Pattern():
                content = pattern.sub(replacement, content)
        path.write_text(content)

    @staticmethod
    def sed_in_place_multi(path: Path, subs: Sequence[tuple[str | re.Pattern[str], str]]) -> None:
        content = path.read_text()
        for pattern, replacement in subs:
            match pattern:
                case str():
                    content = content.replace(pattern, replacement)
                case re.Pattern():
                    content = pattern.sub(replacement, content)
        path.write_text(content)

    def _telemetry_active(self) -> bool:
        """Resolve the tri-state telemetry flag. ``None`` means use the install
        mode default (ON for SOURCE/develop, OFF for PACKAGE)."""
        if self.install_variable.enable_telemetry is not None:
            return self.install_variable.enable_telemetry
        return self.install_info.type == InstallType.SOURCE

    def _enabled_observability_sections(self) -> tuple[str, ...]:
        """Component config sections whose ``enabled = false`` should be flipped
        to ``true`` based on the active observability/telemetry flags."""
        if self.install_variable.enable_observability:
            return ("pyroscope", "otel")
        if self._telemetry_active():
            return ("otel",)
        return ()

    def enable_observability_in_toml(self, path: Path) -> None:
        """Flip ``enabled = false`` to ``enabled = true`` for the relevant
        observability sections of a component config (``[otel]`` always when
        either observability or telemetry is on; ``[pyroscope]`` only when full
        observability is requested). No-op when neither flag is active."""
        sections = self._enabled_observability_sections()
        if not sections:
            return
        content = path.read_text()
        for section in sections:
            section_pat = re.compile(
                rf"(\[{section}\][^\[]*?)^enabled\s*=\s*false",
                re.MULTILINE | re.DOTALL,
            )
            content = section_pat.sub(r"\1enabled = true", content, count=1)
        path.write_text(content)

    async def run_manager_cli(self, cmdargs: Sequence[str]) -> None:
        if self.install_info.type == InstallType.SOURCE:
            # Develop mode: use ./backend.ai from current directory
            cmd_str = " ".join(cmdargs)
            await self.run_shell(f"./backend.ai {cmd_str}")

        elif self.install_info.type == InstallType.PACKAGE:
            # Package mode: use backendai-manager from base_path
            executable = Path(self.install_info.base_path) / "backendai-manager"
            await self.run_exec(
                [str(executable), *cmdargs],
                cwd=self.install_info.base_path,
            )

    @actxmgr
    async def etcd_ctx(self) -> AsyncIterator[AsyncEtcd]:
        halfstack = self.install_info.halfstack_config
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
        }
        creds: dict[str, str] | None = None
        if halfstack.etcd_user is not None:
            if halfstack.etcd_password is None:
                raise ValueError("etcd_password must be set when etcd_user is provided")
            creds = {
                "user": halfstack.etcd_user,
                "password": halfstack.etcd_password,
            }
        async with AsyncEtcd(
            [addr.face for addr in self.install_info.halfstack_config.etcd_addr],
            "local",
            scope_prefix_map,
            credentials=creds,
        ) as etcd:
            yield etcd

    async def etcd_put_json(
        self, key: str, value: Any, *, max_retries: int = 30, retry_interval: float = 2.0
    ) -> None:
        for attempt in range(1, max_retries + 1):
            try:
                async with self.etcd_ctx() as etcd:
                    await etcd.put_prefix(key, value, scope=ConfigScopes.GLOBAL)
                return
            except (GRPCStatusError, ConnectionError, OSError) as e:
                if attempt == max_retries:
                    raise
                self.log.write(
                    f"etcd connection failed ({type(e).__name__}: {e}), "
                    f"retrying ({attempt}/{max_retries})..."
                )
                await asyncio.sleep(retry_interval)

    async def etcd_get_json(self, key: str) -> Any:
        async with self.etcd_ctx() as etcd:
            return await etcd.get_prefix(key, scope=ConfigScopes.GLOBAL)

    async def _ensure_rover_installed(self) -> str:
        rover_bin = Path.home() / ".rover" / "bin" / "rover"

        if rover_bin.exists():
            self.log_header("Rover CLI is already installed.")
            return str(rover_bin)

        if shutil.which("rover"):
            self.log_header("Rover CLI found in PATH.")
            return "rover"

        self.log_header("Installing Rover CLI...")
        install_proc = await asyncio.create_subprocess_shell(
            "curl -sSL https://rover.apollo.dev/nix/latest | sh",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await install_proc.communicate()
        if install_proc.returncode != 0:
            raise RuntimeError(f"Failed to install Rover CLI:\n{stderr.decode()}")

        if not rover_bin.exists():
            raise RuntimeError("Rover CLI installation completed but binary not found.")

        bashrc_path = Path.home() / ".bashrc"
        rover_path_export = 'export PATH="$HOME/.rover/bin:$PATH"'
        license_export = "export APOLLO_ELV2_LICENSE=accept"

        bashrc_content = ""
        if bashrc_path.exists():
            bashrc_content = bashrc_path.read_text()

        lines_to_add = []
        if rover_path_export not in bashrc_content:
            lines_to_add.append(rover_path_export)
        if license_export not in bashrc_content:
            lines_to_add.append(license_export)

        if lines_to_add:
            bashrc_addition = "\n# Added by Backend.AI installer for Rover CLI\n"
            bashrc_addition += "\n".join(lines_to_add) + "\n"

            def _write_bashrc() -> None:
                with bashrc_path.open("a") as f:
                    f.write(bashrc_addition)

            await asyncio.to_thread(_write_bashrc)
            self.log_header("Added Rover PATH and license to ~/.bashrc")

        self.log_header("Rover CLI installed successfully.")
        return str(rover_bin)

    async def install_halfstack(self) -> None:
        self.log_header("Installing halfstack...")

        base_path = self.install_info.base_path

        # Copy gateway config from package resources
        with self.resource_path("ai.backend.install.configs", "gateway.config.ts") as src_gateway:
            dst_gateway = base_path / "gateway.config.ts"
            shutil.copy(src_gateway, dst_gateway)
            self.log_header(f"Copied gateway.config.ts -> {dst_gateway}")

        # Generate or copy supergraph.graphql based on install type
        if self.install_info.type == InstallType.SOURCE:
            # Develop mode: generate supergraph using rover CLI
            self.log_header("Generating supergraph.graphql via rover CLI...")

            rover_path = await self._ensure_rover_installed()

            # Accept ELv2 license for supergraph compose.
            # Although we add this to ~/.bashrc during installation, it won't take effect
            # in the current session, so we must pass it explicitly to the subprocess.
            env = os.environ.copy()
            env["APOLLO_ELV2_LICENSE"] = "accept"

            compose_cmd = [
                rover_path,
                "supergraph",
                "compose",
                "--config",
                "configs/graphql/supergraph.yaml",
            ]
            output_path = "docs/manager/graphql-reference/supergraph.graphql"

            proc = await asyncio.create_subprocess_exec(
                *compose_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to compose supergraph schema:\n{stderr.decode()}")

            def _write_supergraph() -> None:
                with Path(output_path).open("wb") as f:
                    f.write(stdout)

            await asyncio.to_thread(_write_supergraph)
            self.log_header(f"Wrote supergraph schema to {output_path}")

            dst_supergraph = base_path / "supergraph.graphql"
            shutil.copy(Path(output_path), dst_supergraph)
            self.log_header(f"Copied supergraph.graphql -> {dst_supergraph}")
        else:
            # Package mode: download supergraph from GitHub releases
            from ai.backend.install import __version__

            self.log_header("Downloading supergraph.graphql from GitHub releases...")

            # Construct URL for the release version. Release tags carry no "v"
            # prefix (e.g. "26.4.4rc9"), matching _fetch_package's download URL.
            version_tag = __version__
            url = (
                f"https://raw.githubusercontent.com/lablup/backend.ai/{version_tag}/"
                "docs/manager/graphql-reference/supergraph.graphql"
            )

            dst_supergraph = base_path / "supergraph.graphql"
            await wget(url, dst_supergraph)
            self.log_header(f"Downloaded supergraph.graphql -> {dst_supergraph}")

        # Copy from install package as docker-compose.yml, then rename to
        # docker-compose.halfstack.current.yml so the file name matches the convention
        # used by other dev scripts (start-dev.sh, refresh-graphql-gateway.sh, etc.).
        src_compose_path = self.copy_config("docker-compose.yml")
        dst_compose_path = src_compose_path.with_name("docker-compose.halfstack.current.yml")
        src_compose_path.rename(dst_compose_path)
        self.copy_config("prometheus.yaml")
        self.copy_config("grafana-dashboards")
        self.copy_config("grafana-provisioning")
        self.copy_config("otel-collector-config.yaml")
        self.copy_config("loki-config.yaml")
        self.copy_config("tempo-config.yaml")

        volume_path = self.install_info.base_path / "volumes"
        (volume_path / "postgres-data").mkdir(parents=True, exist_ok=True)
        (volume_path / "etcd-data").mkdir(parents=True, exist_ok=True)
        (volume_path / "redis-data").mkdir(parents=True, exist_ok=True)
        (volume_path / "grafana-data").mkdir(parents=True, exist_ok=True)

        # TODO: implement ha setup
        if not self.install_info.halfstack_config.redis_addr:
            raise RuntimeError("redis_addr must be configured")
        self.sed_in_place_multi(
            dst_compose_path,
            [
                ("8100:5432", f"{self.install_info.halfstack_config.postgres_addr.bind.port}:5432"),
                ("8110:6379", f"{self.install_info.halfstack_config.redis_addr.bind.port}:6379"),
                ("8120:2379", f"{self.install_info.halfstack_config.etcd_addr[0].bind.port}:2379"),
            ],
        )
        sudo = " ".join(self.docker_sudo)
        profile_args_list: list[str] = []
        if self.install_variable.enable_observability:
            # observability profile is a superset of telemetry; no need to add both.
            profile_args_list.append("--profile observability")
        elif self._telemetry_active():
            profile_args_list.append("--profile telemetry")
        if self.install_variable.enable_storage:
            profile_args_list.append("--profile storage")
        profile_args = " ".join(profile_args_list)
        compose_file_arg = "-f docker-compose.halfstack.current.yml"
        await self.run_shell(
            f"""
        {sudo} docker compose {compose_file_arg} {profile_args} pull && \\
        {sudo} docker compose {compose_file_arg} {profile_args} up -d --wait backendai-half-db && \\
        {sudo} docker compose {compose_file_arg} {profile_args} up -d --wait && \\
        {sudo} docker compose {compose_file_arg} {profile_args} ps
        """,
            cwd=self.install_info.base_path,
        )

    async def load_fixtures(self) -> None:
        with self.resource_path("ai.backend.install.fixtures", "example-users.json") as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])

        with self.resource_path(
            "ai.backend.install.fixtures", "example-container-registries-harbor.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])

        with self.resource_path("ai.backend.install.fixtures", "example-keypairs.json") as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-set-user-main-access-keys.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-resource-slot-types.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-resource-presets.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-runtime-variants.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-runtime-variant-presets.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path("ai.backend.install.fixtures", "example-roles.json") as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-prometheus-query-preset-categories.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-prometheus-query-presets.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])

    async def check_prerequisites(self) -> None:
        self.os_info = await detect_os()
        text = Text()
        text.append("Detected OS info: ")
        text.append(self.os_info.__rich__())  # type: ignore
        self.log.write(text)
        if "LiveCD" in self.os_info.distro_variants:
            self.log.write(
                Text.from_markup(
                    "[yellow bold]:warning: You are running under a temporary LiveCD/USB boot"
                    " environment.[/]"
                )
            )
            self.log.write(
                Text.from_markup(
                    "[yellow]Ensure that you have enough RAM disk space more than 10 GiB.[/]"
                )
            )
            await self.log.wait_continue()
        if "WSL" in self.os_info.distro_variants:
            self.log.write(
                Text.from_markup(
                    "[yellow bold]:warning: You are running under a WSL environment.[/]"
                )
            )
            # TODO: update the docs link
            self.log.write(
                Text.from_markup(
                    "[yellow]Checkout additional pre-setup guide for WSL:"
                    " https://docs.backend.ai/en/latest/install/env-wsl2.html[/]"
                )
            )
            await self.log.wait_continue()
        if await determine_docker_sudo():
            self.docker_sudo = ["sudo"]
            self.log.write(
                Text.from_markup(
                    "[yellow]The Docker API and commands require sudo. We will use sudo.[/]"
                )
            )
        else:
            self.docker_sudo = []
        await check_docker(self)
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount(self)

    async def configure_manager(self) -> None:
        base_path = self.install_info.base_path
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        toml_path = self.copy_config("manager.toml")
        alembic_path = self.copy_config("alembic.ini")
        (base_path / "fixtures" / "manager").mkdir(parents=True, exist_ok=True)
        await self.run_manager_cli(["mgr", "generate-rpc-keypair", "fixtures/manager", "manager"])
        self.sed_in_place_multi(
            toml_path,
            [
                (re.compile("^num-proc = .*", flags=re.MULTILINE), "num-proc = 1"),
                ("port = 8120", f"port = {halfstack.etcd_addr[0].face.port}"),
                ("port = 8100", f"port = {halfstack.postgres_addr.face.port}"),
                (
                    "port = 8081",
                    f"port = {self.install_info.service_config.manager_addr.bind.port}",
                ),
                (
                    re.compile("^(# )?ipc-base-path =.*", flags=re.MULTILINE),
                    f'ipc-base-path = "{self.install_info.service_config.manager_ipc_base_path}"',
                ),
            ],
        )
        self.sed_in_place(
            alembic_path,
            "localhost:8100",
            f"{halfstack.postgres_addr.face.host}:{halfstack.postgres_addr.face.port}",
        )
        await asyncio.sleep(0)
        storage_client_facing_addr = service.storage_proxy_client_facing_addr
        storage_manager_facing_addr = service.storage_proxy_manager_facing_addr
        data: Any = {
            "volumes": {
                "_types": {"group": "", "user": ""},
                "default_host": "local:volume1",
                "proxies": {
                    "local": {
                        "client_api": f"http://{storage_client_facing_addr.face.host}:{storage_client_facing_addr.face.port}",
                        "manager_api": f"https://{storage_manager_facing_addr.face.host}:{storage_manager_facing_addr.face.port}",
                        "secret": self.install_info.service_config.storage_proxy_manager_auth_key,
                        "ssl_verify": "false",
                    }
                },
                "exposed_volume_info": "percentage",
            },
        }
        # When a dedicated SFTP agent is configured, point the storage proxy's
        # sftp_scaling_groups at that agent's scaling group so that SFTP
        # upload sessions get routed through it.
        # Must be under volumes/proxies/<proxy>/ per manager config schema.
        if service.sftp_agent_enabled:
            data["volumes"]["proxies"]["local"]["sftp_scaling_groups"] = (
                service.sftp_agent_scaling_group
            )
        await self.etcd_put_json("", data)
        data = {}
        # TODO: in dev-mode, enable these.
        data["api"] = {}
        data["api"]["allow-openapi-schema-introspection"] = "no"
        data["api"]["allow-graphql-schema-introspection"] = "no"
        if halfstack.ha_setup:
            if not halfstack.redis_sentinel_addrs:
                raise RuntimeError("redis_sentinel_addrs must be configured for HA setup")
            data["redis"] = {
                "sentinel": ",".join(
                    f"{binding.host}:{binding.port}" for binding in halfstack.redis_sentinel_addrs
                ),
                "service_name": "mymaster",
                "helper": {
                    "socket_timeout": 5.0,
                    "socket_connect_timeout": 2.0,
                    "reconnect_poll_timeout": 0.3,
                },
            }
            if halfstack.redis_password:
                data["redis"]["password"] = halfstack.redis_password
        else:
            if not halfstack.redis_addr:
                raise RuntimeError("redis_addr must be configured")
            data["redis"] = {
                "addr": f"{halfstack.redis_addr.face.host}:{halfstack.redis_addr.face.port}",
                "helper": {
                    "socket_timeout": 5.0,
                    "socket_connect_timeout": 2.0,
                    "reconnect_poll_timeout": 0.3,
                },
            }
            if halfstack.redis_password:
                data["redis"]["password"] = halfstack.redis_password
        (base_path / "etcd.config.json").write_text(json.dumps(data))
        await self.etcd_put_json("config", data)
        public_addr = self.install_variable.public_facing_address
        manager_port = self.install_info.service_config.manager_addr.bind.port
        self.sed_in_place(
            toml_path,
            re.compile(r"^internal-addr = .*$", flags=re.MULTILINE),
            f'internal-addr = {{ host = "0.0.0.0", port = 18080 }}\n'
            f'announce-addr = {{ host = "{public_addr}", port = {manager_port} }}\n'
            f'announce-internal-addr = {{ host = "{public_addr}", port = 18080 }}',
        )
        if self.install_variable.otel_endpoint:
            self.sed_in_place(
                toml_path,
                'endpoint = "http://127.0.0.1:4317"',
                f'endpoint = "{self.install_variable.otel_endpoint}"',
            )
        self.enable_observability_in_toml(toml_path)

    async def configure_agent(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        accelerator = self.install_info.accelerator
        toml_path = self.copy_config("agent.toml")
        self.sed_in_place_multi(
            toml_path,
            [
                ("port = 8120", f"port = {halfstack.etcd_addr[0].face.port}"),
                ("port = 6001", f"port = {service.agent_rpc_addr.bind.port}"),
                ("port = 6009", f"port = {service.agent_watcher_addr.bind.port}"),
                (
                    re.compile("^(# )?ipc-base-path = .*", flags=re.MULTILINE),
                    f'ipc-base-path = "{service.agent_ipc_base_path}"',
                ),
                (
                    re.compile("^(# )?var-base-path = .*", flags=re.MULTILINE),
                    f'var-base-path = "{service.agent_var_base_path}"',
                ),
                (
                    re.compile("(# )?mount_path = .*", flags=re.MULTILINE),
                    f'"{self.install_info.base_path / service.vfolder_relpath}"',
                ),
            ],
        )
        Path(self.install_info.service_config.agent_var_base_path).mkdir(
            parents=True, exist_ok=True
        )
        if accelerator is not None:
            if accelerator == Accelerator.CUDA:
                plugin_list = ['"ai.backend.accelerator.cuda_open"']
            elif accelerator in (
                Accelerator.CUDA_MOCK,
                Accelerator.CUDA_MIG_MOCK,
                Accelerator.ROCM_MOCK,
            ):
                plugin_list = ['"ai.backend.accelerator.mock"']
            else:
                plugin_list = []

            await self._configure_mock_accelerator(accelerator)
        else:
            plugin_list = []

        self.sed_in_place(
            toml_path,
            re.compile(r"^(# )?allow-compute-plugins = .*", flags=re.MULTILINE),
            f"allow-compute-plugins = [{', '.join(plugin_list)}]",
        )
        public_addr = self.install_variable.public_facing_address
        self.sed_in_place(
            toml_path,
            re.compile(
                r'^service-addr = \{ host = "0\.0\.0\.0", port = 6003 \}', flags=re.MULTILINE
            ),
            f'service-addr = {{ host = "0.0.0.0", port = 6003 }}\n'
            f'announce-addr = {{ host = "{public_addr}", port = 6003 }}',
        )
        if self.install_variable.otel_endpoint:
            self.sed_in_place(
                toml_path,
                'endpoint = "http://127.0.0.1:4317"',
                f'endpoint = "{self.install_variable.otel_endpoint}"',
            )
        self.enable_observability_in_toml(toml_path)

    async def configure_sftp_agent(self) -> None:
        """
        Configure an optional dedicated SFTP agent alongside the regular
        compute agent. This is gated by ``install_variable.with_sftp_agent``
        and piggybacks on Backend.AI's multi-agent-per-node feature.

        Clones the already-generated ``./agent.toml`` (produced by
        ``configure_agent``) so that etcd, mount-path, plugin, and other
        environment-specific settings are automatically shared.  Then
        applies SFTP-specific overrides (distinct ports, pid-file,
        scaling-group, ipc/var paths) so the two agents can coexist on
        the same node without resource collisions.
        """
        service = self.install_info.service_config
        if not service.sftp_agent_enabled:
            return

        # Clone the primary agent config instead of the bundled template
        # so that every environment-dependent setting (etcd addr, mount-path,
        # accelerator plugins, etc.) is inherited automatically.
        primary_toml = Path.cwd() / "agent.toml"
        toml_path = Path.cwd() / "agent-sftp.toml"
        shutil.copy2(primary_toml, toml_path)
        Path(service.sftp_agent_var_base_path).mkdir(parents=True, exist_ok=True)

        self.sed_in_place_multi(
            toml_path,
            [
                # --- port collision avoidance ---
                (
                    f"port = {service.agent_rpc_addr.face.port}",
                    f"port = {service.sftp_agent_rpc_addr.face.port}",
                ),
                (
                    f"agent-sock-port = {service.agent_sock_port}",
                    f"agent-sock-port = {service.sftp_agent_sock_port}",
                ),
                (
                    f"port = {service.agent_watcher_addr.face.port}",
                    f"port = {service.sftp_agent_watcher_addr.face.port}",
                ),
                # --- identity ---
                (
                    re.compile(r'^# id = "i-something-special"', flags=re.MULTILINE),
                    'id = "i-local-sftp"',
                ),
                (re.compile(r'^id = "i-.*"', flags=re.MULTILINE), 'id = "i-local-sftp"'),
                (
                    f'scaling-group = "{service.scaling_group}"',
                    f'scaling-group = "{service.sftp_agent_scaling_group}"',
                ),
                # --- path isolation ---
                ('pid-file = "./agent.pid"', 'pid-file = "./agent-sftp.pid"'),
                (
                    f'ipc-base-path = "{service.agent_ipc_base_path}"',
                    f'ipc-base-path = "{service.sftp_agent_ipc_base_path}"',
                ),
                (
                    f'var-base-path = "{service.agent_var_base_path}"',
                    f'var-base-path = "{service.sftp_agent_var_base_path}"',
                ),
                # --- metric API service-addr (avoid port 6003 collision) ---
                (
                    'service-addr = { host = "0.0.0.0", port = 6003 }',
                    'service-addr = { host = "0.0.0.0", port = 6014 }',
                ),
                # --- container port range (non-overlapping) ---
                ("port-range = [30000, 31000]", "port-range = [31100, 31200]"),
                # --- disable compute plugins (SFTP only) ---
                (
                    re.compile(r"^allow-compute-plugins = \[.*\]", flags=re.MULTILINE),
                    "allow-compute-plugins = []",
                ),
                # --- pyroscope differentiation ---
                ('app-name = "backendai-half-agent"', 'app-name = "backendai-half-sftp-agent"'),
            ],
        )
        # Insert additional ports into [agent] section to avoid collision
        # with the primary agent (aiomonitor defaults: 38200/39200,
        # metadata-server-port default: 40128).
        self.sed_in_place_multi(
            toml_path,
            [
                (
                    'id = "i-local-sftp"',
                    (
                        'id = "i-local-sftp"\n'
                        "aiomonitor-termui-port = 38201\n"
                        "aiomonitor-webui-port = 39201\n"
                        "metadata-server-port = 40129"
                    ),
                ),
            ],
        )

    async def configure_storage_proxy(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        toml_path = self.copy_config("storage-proxy.toml")

        ssl_dir = self.install_info.base_path / "configs" / "storage-proxy" / "ssl"
        ssl_dir.mkdir(parents=True, exist_ok=True)
        cert_path = ssl_dir / "manager-api-selfsigned.cert.pem"
        key_path = ssl_dir / "manager-api-selfsigned.key.pem"

        # TODO: If the user disables SSL in the configuration, skip creating the PEM files.
        self.log_header("Generating self-signed SSL certificate for storage-proxy (manager API)...")
        public_addr = self.install_variable.public_facing_address
        subj = f"/C=KR/ST=Seoul/L=Seoul/O=BackendAI/OU=StorageProxy/CN={public_addr}"
        proc = await asyncio.create_subprocess_exec(
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(key_path),
            "-out",
            str(cert_path),
            "-days",
            "3650",
            "-nodes",
            "-subj",
            subj,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"Failed to generate the storage-proxy self-signed certificate "
                f"(openssl exit {proc.returncode}):\n{stderr.decode(errors='replace')}"
            )
        self.log.write(Text.from_markup(f"Created SSL cert/key under {ssl_dir}"))

        with toml_path.open("r") as fp:
            data = tomlkit.load(fp)
            etcd_table = tomlkit.table()
            etcd_addr_table = tomlkit.inline_table()
            etcd_addr_table["host"] = halfstack.etcd_addr[0].face.host
            etcd_addr_table["port"] = halfstack.etcd_addr[0].face.port
            etcd_table["addr"] = etcd_addr_table
            etcd_table["namespace"] = "local"
            if halfstack.etcd_user:
                etcd_table["user"] = halfstack.etcd_user
            else:
                etcd_table.pop("user", None)
            if halfstack.etcd_password:
                etcd_table["password"] = halfstack.etcd_password
            else:
                etcd_table.pop("password", None)
            data["etcd"] = etcd_table
            data["storage-proxy"]["secret"] = service.storage_proxy_random  # type: ignore
            data["storage-proxy"]["ipc-base-path"] = service.storage_proxy_ipc_base_path  # type: ignore
            client_facing_addr_table = tomlkit.inline_table()
            client_facing_addr_table["host"] = service.storage_proxy_client_facing_addr.bind.host
            client_facing_addr_table["port"] = service.storage_proxy_client_facing_addr.bind.port
            data["api"]["client"]["service-addr"] = client_facing_addr_table  # type: ignore
            manager_facing_addr_table = tomlkit.inline_table()
            manager_facing_addr_table["host"] = service.storage_proxy_manager_facing_addr.bind.host
            manager_facing_addr_table["port"] = service.storage_proxy_manager_facing_addr.bind.port
            data["api"]["manager"]["service-addr"] = manager_facing_addr_table  # type: ignore
            data["api"]["manager"]["secret"] = service.storage_proxy_manager_auth_key  # type: ignore
            announce_addr_table = tomlkit.inline_table()
            announce_addr_table["host"] = self.install_variable.public_facing_address
            announce_addr_table["port"] = service.storage_proxy_manager_facing_addr.bind.port
            data["api"]["manager"]["announce-addr"] = announce_addr_table  # type: ignore
            announce_internal_table = tomlkit.inline_table()
            announce_internal_table["host"] = self.install_variable.public_facing_address
            announce_internal_table["port"] = 16023
            data["api"]["manager"]["announce-internal-addr"] = announce_internal_table  # type: ignore
            data["volume"]["volume1"]["path"] = service.vfolder_relpath  # type: ignore
        with toml_path.open("w") as fp:
            tomlkit.dump(data, fp)
        if self.install_variable.otel_endpoint:
            self.sed_in_place(
                toml_path,
                'endpoint = "http://127.0.0.1:4317"',
                f'endpoint = "{self.install_variable.otel_endpoint}"',
            )
        self.enable_observability_in_toml(toml_path)

    async def configure_webserver(self) -> None:
        conf_path = self.copy_config("webserver.conf")
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        endpoint_protocol = self.install_variable.endpoint_protocol
        fqdn_prefix = self.install_variable.fqdn_prefix
        storage_public_address = self.install_variable.storage_public_address
        public_facing_address = self.install_variable.public_facing_address
        if halfstack.redis_addr is None:
            raise RuntimeError("redis_addr must be configured")

        # use FQDN if provided, otherwise use public_facing_address
        if fqdn_prefix is not None:
            # With FQDN prefix, use public storage address with https
            wsproxy_url = f"https://{storage_public_address}:5050"
        else:
            # Without FQDN prefix, use public_facing_address with http
            wsproxy_url = f"http://{public_facing_address}:5050"
        # Use sed_in_place for dotted key wsproxy.url
        self.sed_in_place(
            conf_path,
            re.compile(r'^wsproxy\.url\s*=\s*".*"', flags=re.MULTILINE),
            f'wsproxy.url = "{wsproxy_url}"',
        )

        with conf_path.open("r") as fp:
            data = tomlkit.load(fp)
            if endpoint_protocol is not None:
                data["service"]["force_endpoint_protocol"] = endpoint_protocol.value  # type: ignore
            data["api"][  # type: ignore
                "endpoint"
            ] = f"http://{service.manager_addr.face.host}:{service.manager_addr.face.port}"
            helper_table = tomlkit.table()
            helper_table["socket_timeout"] = 5.0
            helper_table["socket_connect_timeout"] = 2.0
            helper_table["reconnect_poll_timeout"] = 0.3
            if halfstack.ha_setup:
                if not halfstack.redis_sentinel_addrs:
                    raise ValueError("Redis sentinel addresses must be configured for HA setup")
                redis_table = tomlkit.table()
                redis_table["sentinel"] = ",".join(
                    f"{binding.host}:{binding.port}" for binding in halfstack.redis_sentinel_addrs
                )
                redis_table["service_name"] = "mymaster"
                redis_table["redis_helper_config"] = helper_table
                if halfstack.redis_password:
                    redis_table["password"] = halfstack.redis_password
            else:
                if not halfstack.redis_addr:
                    raise RuntimeError("redis_addr must be configured")
                redis_table = tomlkit.table()
                redis_table["addr"] = (
                    f"{halfstack.redis_addr.face.host}:{halfstack.redis_addr.face.port}"
                )
                redis_table["redis_helper_config"] = helper_table
                if halfstack.redis_password:
                    redis_table["password"] = halfstack.redis_password
            data["session"]["redis"] = redis_table  # type: ignore
            data["ui"]["menu_blocklist"] = ",".join(service.webui_menu_blocklist)  # type: ignore
            data["ui"]["menu_inactivelist"] = ",".join(service.webui_menu_inactivelist)  # type: ignore
        with conf_path.open("w") as fp:
            tomlkit.dump(data, fp)
        if self.install_variable.otel_endpoint:
            self.sed_in_place(
                conf_path,
                'endpoint = "http://127.0.0.1:4317"',
                f'endpoint = "{self.install_variable.otel_endpoint}"',
            )
        self.enable_observability_in_toml(conf_path)

    async def configure_webui(self) -> None:
        dotenv_path = self.install_info.base_path / ".env"
        service = self.install_info.service_config
        envs = [
            f"PROXYLISTENIP={service.local_proxy_addr.bind.host}",
            f"PROXYBASEHOST={service.local_proxy_addr.face.host}",
            f"PROXYBASEPORT={service.local_proxy_addr.face.port}",
            "",
        ]
        dotenv_path.write_text("\n".join(envs))

    async def install_appproxy_db(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config

        self.log_header("Setting up databases... (app-proxy)")

        # 1. Connect to core DB
        core_conn = await asyncpg.connect(
            host=halfstack.postgres_addr.face.host,
            port=halfstack.postgres_addr.face.port,
            user=halfstack.postgres_user,
            password=halfstack.postgres_password,
            database="backend",
        )

        # 2. Create role/database if not exist
        await core_conn.execute(
            """
            DO $$
            BEGIN
               IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'appproxy') THEN
                  CREATE ROLE appproxy WITH LOGIN PASSWORD 'develove';
               ELSE
                  ALTER ROLE appproxy WITH LOGIN PASSWORD 'develove';
               END IF;
            END
            $$;
            """
        )
        exists = await core_conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'appproxy'")
        if not exists:
            await core_conn.execute("CREATE DATABASE appproxy OWNER appproxy;")
        await core_conn.execute("GRANT ALL PRIVILEGES ON DATABASE appproxy TO appproxy;")
        await core_conn.close()

        # 3. Grant privileges
        app_conn = await asyncpg.connect(
            host=halfstack.postgres_addr.face.host,
            port=halfstack.postgres_addr.face.port,
            user=halfstack.postgres_user,
            password=halfstack.postgres_password,
            database="appproxy",
        )
        await app_conn.execute("GRANT ALL ON SCHEMA public TO appproxy;")
        await app_conn.close()

        # 4. Run Alembic migration for app-proxy
        alembic_ini = self.copy_config("alembic-appproxy.ini")
        await self.run_exec(
            [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
            cwd=self.install_info.base_path,
        )

        # 5. Update scaling_groups in core DB
        # TODO: Still using wsproxy_* columns for backward compatibility (same with install-dev.sh logic)
        core_conn = await asyncpg.connect(
            host=halfstack.postgres_addr.face.host,
            port=halfstack.postgres_addr.face.port,
            user=halfstack.postgres_user,
            password=halfstack.postgres_password,
            database="backend",
        )
        await core_conn.execute(
            """
            UPDATE scaling_groups
            SET wsproxy_api_token = $1,
                wsproxy_addr = $2
            WHERE name = 'default'
            """,
            service.appproxy_api_secret,
            f"http://{service.appproxy_coordinator_addr.face.host}:{service.appproxy_coordinator_addr.face.port}",
        )
        await core_conn.close()

    async def configure_appproxy(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config

        # Coordinator
        coord_conf = self.copy_config("app-proxy-coordinator.toml")

        self.log.write(f"DB HOST = {halfstack.postgres_addr.face.host}")
        self.log.write(f"DB PORT = {halfstack.postgres_addr.face.port}")
        self.log.write(f"API SECRET = {service.appproxy_api_secret}")

        tls_advertised = self.install_variable.tls_advertised
        advertised_port = self.install_variable.advertised_port
        wildcard_domain = self.install_variable.wildcard_domain
        public_facing_address = self.install_variable.public_facing_address
        apphub_address = self.install_variable.apphub_address
        app_address = self.install_variable.app_address
        frontend_mode = self.install_variable.frontend_mode

        with coord_conf.open("r") as fp:
            data = tomlkit.load(fp)
            data["db"]["type"] = "postgresql"  # type: ignore[index]
            data["db"]["name"] = "appproxy"  # type: ignore[index]
            data["db"]["user"] = "appproxy"  # type: ignore[index]
            data["db"]["password"] = "develove"  # type: ignore[index]
            data["db"]["pool_size"] = 8  # type: ignore[index]
            data["db"]["max_overflow"] = 64  # type: ignore[index]
            data["db"]["addr"]["host"] = halfstack.postgres_addr.face.host  # type: ignore[index]
            data["db"]["addr"]["port"] = halfstack.postgres_addr.face.port  # type: ignore[index]
            redis_addr_table = tomlkit.inline_table()
            redis_addr_table["host"] = halfstack.redis_addr.face.host
            redis_addr_table["port"] = halfstack.redis_addr.face.port
            data["redis"]["addr"] = redis_addr_table  # type: ignore[index]
            data["secrets"]["api_secret"] = service.appproxy_api_secret  # type: ignore[index]
            data["secrets"]["jwt_secret"] = service.appproxy_jwt_secret  # type: ignore[index]
            data["permit_hash"]["secret"] = service.appproxy_permit_hash_secret  # type: ignore[index]
            data["proxy_coordinator"]["bind_addr"]["host"] = "0.0.0.0"  # type: ignore[index]
            data["proxy_coordinator"]["bind_addr"]["port"] = (  # type: ignore[index]
                service.appproxy_coordinator_addr.bind.port
            )
            data["proxy_coordinator"]["advertised_addr"]["host"] = apphub_address  # type: ignore[index]
            data["proxy_coordinator"]["advertised_addr"]["port"] = (  # type: ignore[index]
                service.appproxy_coordinator_addr.bind.port
            )
            if tls_advertised:
                data["proxy_coordinator"]["tls_advertised"] = True  # type: ignore[index]
                data["proxy_coordinator"]["advertised_addr"]["port"] = advertised_port  # type: ignore[index]
            data["proxy_coordinator"]["metric_access_allowed_hosts"] = (  # type: ignore[index]
                self.install_variable.metric_access_cidr
            )
        with coord_conf.open("w") as fp:
            tomlkit.dump(data, fp)

        # Worker
        worker_conf = self.copy_config("app-proxy-worker.toml")
        with worker_conf.open("r") as fp:
            data = tomlkit.load(fp)
            # Update redis addr inline table
            redis_addr_table = tomlkit.inline_table()
            redis_addr_table["host"] = halfstack.redis_addr.face.host
            redis_addr_table["port"] = halfstack.redis_addr.face.port
            data["redis"]["addr"] = redis_addr_table  # type: ignore[index]

            data["proxy_worker"]["coordinator_endpoint"] = (  # type: ignore[index]
                f"http://{service.appproxy_coordinator_addr.bind.host}:{service.appproxy_coordinator_addr.bind.port}"
            )

            # api_bind_addr as inline table
            api_bind_addr_table = tomlkit.inline_table()
            api_bind_addr_table["host"] = service.appproxy_worker_addr.bind.host
            api_bind_addr_table["port"] = service.appproxy_worker_addr.bind.port
            data["proxy_worker"]["api_bind_addr"] = api_bind_addr_table  # type: ignore[index]

            # api_advertised_addr as inline table
            api_advertised_addr_table = tomlkit.inline_table()
            api_advertised_addr_table["host"] = public_facing_address
            api_advertised_addr_table["port"] = service.appproxy_worker_addr.bind.port
            data["proxy_worker"]["api_advertised_addr"] = api_advertised_addr_table  # type: ignore[index]

            data["secrets"]["api_secret"] = service.appproxy_api_secret  # type: ignore[index]
            data["secrets"]["jwt_secret"] = service.appproxy_jwt_secret  # type: ignore[index]
            data["permit_hash"]["secret"] = service.appproxy_permit_hash_secret  # type: ignore[index]

            # advertise TLS to external clients
            if tls_advertised:
                data["proxy_worker"]["tls_advertised"] = True  # type: ignore[index]

            # set frontend mode (port or wildcard)
            data["proxy_worker"]["frontend_mode"] = frontend_mode.value  # type: ignore[index]

            # configure based on frontend_mode
            if frontend_mode == FrontendMode.WILDCARD:
                # Remove port_proxy section for wildcard mode
                if "port_proxy" in data["proxy_worker"]:  # type: ignore[operator]
                    del data["proxy_worker"]["port_proxy"]

                # Override api_advertised_addr with app_address and advertised_port
                api_advertised_addr_table = tomlkit.inline_table()
                api_advertised_addr_table["host"] = app_address
                api_advertised_addr_table["port"] = advertised_port
                data["proxy_worker"]["api_advertised_addr"] = api_advertised_addr_table  # type: ignore[index]

                # Add wildcard_domain section
                if wildcard_domain:
                    wildcard_table = tomlkit.table()
                    wildcard_table["domain"] = wildcard_domain
                    bind_addr_table = tomlkit.inline_table()
                    bind_addr_table["host"] = "0.0.0.0"
                    bind_addr_table["port"] = 10250
                    wildcard_table["bind_addr"] = bind_addr_table
                    wildcard_table["advertised_port"] = advertised_port
                    wildcard_table.add(tomlkit.nl())  # Add newline before next section
                    data["proxy_worker"]["wildcard_domain"] = wildcard_table  # type: ignore[index]
            else:
                # update port_proxy.advertised_host
                data["proxy_worker"]["port_proxy"]["advertised_host"] = public_facing_address  # type: ignore[index]
            data["proxy_worker"]["metric_access_allowed_hosts"] = (  # type: ignore[index]
                self.install_variable.metric_access_cidr
            )
        with worker_conf.open("w") as fp:
            tomlkit.dump(data, fp)

        # TCP Worker
        tcp_worker_conf = self.copy_config("app-proxy-worker-tcp.toml")
        with tcp_worker_conf.open("r") as fp:
            data = tomlkit.load(fp)
            redis_addr_table = tomlkit.inline_table()
            redis_addr_table["host"] = halfstack.redis_addr.face.host
            redis_addr_table["port"] = halfstack.redis_addr.face.port
            data["redis"]["addr"] = redis_addr_table  # type: ignore[index]

            data["proxy_worker"]["coordinator_endpoint"] = (  # type: ignore[index]
                f"http://{service.appproxy_coordinator_addr.bind.host}:{service.appproxy_coordinator_addr.bind.port}"
            )

            api_bind_addr_table = tomlkit.inline_table()
            api_bind_addr_table["host"] = service.appproxy_tcp_worker_addr.bind.host
            api_bind_addr_table["port"] = service.appproxy_tcp_worker_addr.bind.port
            data["proxy_worker"]["api_bind_addr"] = api_bind_addr_table  # type: ignore[index]

            api_advertised_addr_table = tomlkit.inline_table()
            api_advertised_addr_table["host"] = public_facing_address
            api_advertised_addr_table["port"] = service.appproxy_tcp_worker_addr.bind.port
            data["proxy_worker"]["api_advertised_addr"] = api_advertised_addr_table  # type: ignore[index]

            data["secrets"]["api_secret"] = service.appproxy_api_secret  # type: ignore[index]
            data["secrets"]["jwt_secret"] = service.appproxy_jwt_secret  # type: ignore[index]
            data["permit_hash"]["secret"] = service.appproxy_permit_hash_secret  # type: ignore[index]

            if tls_advertised:
                data["proxy_worker"]["tls_advertised"] = True  # type: ignore[index]

            data["proxy_worker"]["frontend_mode"] = frontend_mode.value  # type: ignore[index]

            if frontend_mode == FrontendMode.WILDCARD:
                if "port_proxy" in data["proxy_worker"]:  # type: ignore[operator]
                    del data["proxy_worker"]["port_proxy"]
                api_advertised_addr_table = tomlkit.inline_table()
                api_advertised_addr_table["host"] = app_address
                api_advertised_addr_table["port"] = advertised_port
                data["proxy_worker"]["api_advertised_addr"] = api_advertised_addr_table  # type: ignore[index]
                if wildcard_domain:
                    wildcard_table = tomlkit.table()
                    wildcard_table["domain"] = wildcard_domain
                    bind_addr_table = tomlkit.inline_table()
                    bind_addr_table["host"] = "0.0.0.0"
                    bind_addr_table["port"] = 10550
                    wildcard_table["bind_addr"] = bind_addr_table
                    wildcard_table["advertised_port"] = advertised_port
                    wildcard_table.add(tomlkit.nl())
                    data["proxy_worker"]["wildcard_domain"] = wildcard_table  # type: ignore[index]
            else:
                data["proxy_worker"]["port_proxy"]["advertised_host"] = public_facing_address  # type: ignore[index]
        with tcp_worker_conf.open("w") as fp:
            tomlkit.dump(data, fp)

        # Alembic migration config
        alembic_cfg = self.copy_config("alembic-appproxy.ini")
        self.sed_in_place_multi(
            alembic_cfg,
            [
                (
                    "localhost:8100",
                    f"{halfstack.postgres_addr.face.host}:{halfstack.postgres_addr.face.port}",
                ),
                (
                    re.compile(r"^#?sqlalchemy.url\s*=.*", flags=re.MULTILINE),
                    f"sqlalchemy.url = postgresql+asyncpg://appproxy:develove@{halfstack.postgres_addr.face.host}:{halfstack.postgres_addr.face.port}/appproxy",
                ),
            ],
        )
        if self.install_variable.otel_endpoint:
            for conf in (coord_conf, worker_conf):
                self.sed_in_place(
                    conf,
                    'endpoint = "http://127.0.0.1:4317"',
                    f'endpoint = "{self.install_variable.otel_endpoint}"',
                )
        for conf in (coord_conf, worker_conf):
            self.enable_observability_in_toml(conf)

    async def configure_appproxy_fixture(self) -> None:
        self.log_header("Updating manager scaling_groups to point to appproxy coordinator...")

        service = self.install_info.service_config
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "fixture.json"
            with fixture_path.open("w") as fw:
                fw.write(
                    json.dumps({
                        "__mode": "update",
                        "scaling_groups": [
                            {
                                "name": "default",
                                "wsproxy_addr": f"http://{service.appproxy_coordinator_addr.face.host}:{service.appproxy_coordinator_addr.face.port}",
                                "wsproxy_api_token": service.appproxy_api_secret,
                            }
                        ],
                    })
                )
            await self.run_manager_cli(["mgr", "fixture", "populate", fixture_path.as_posix()])

    async def configure_sftp_agent_fixture(self) -> None:
        """
        Register the dedicated SFTP scaling group and associate it with the
        default domain. This is only populated when the user passed
        ``--with-sftp-agent`` — it mirrors the ``sgroups_for_domains``
        association in ``example-users.json`` for the default scaling group.
        """
        service = self.install_info.service_config
        if not service.sftp_agent_enabled:
            return

        self.log_header(
            f"Registering '{service.sftp_agent_scaling_group}' scaling group for SFTP agent..."
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "fixture.json"
            with fixture_path.open("w") as fw:
                fw.write(
                    json.dumps({
                        "scaling_groups": [
                            {
                                "name": service.sftp_agent_scaling_group,
                                "description": "Scaling group dedicated to SFTP upload sessions",
                                "is_active": True,
                                "driver": "static",
                                "driver_opts": {},
                                "scheduler": "fifo",
                                "scheduler_opts": {},
                                "wsproxy_addr": (
                                    f"http://{service.appproxy_coordinator_addr.face.host}"
                                    f":{service.appproxy_coordinator_addr.face.port}"
                                ),
                                "wsproxy_api_token": service.appproxy_api_secret,
                            }
                        ],
                        "sgroups_for_domains": [
                            {
                                "scaling_group": service.sftp_agent_scaling_group,
                                "domain": "default",
                            }
                        ],
                    })
                )
            await self.run_manager_cli(["mgr", "fixture", "populate", fixture_path.as_posix()])

    async def configure_client(self) -> None:
        # TODO: add an option to generate keypairs
        base_path = self.install_info.base_path
        service = self.install_info.service_config
        with self.resource_path(
            "ai.backend.install.fixtures", "example-keypairs.json"
        ) as keypair_path:
            keypair_data = json.loads(Path(keypair_path).read_bytes())
        for keypair in keypair_data["keypairs"]:
            email = keypair["user_id"]
            if match := re.search(r"^(\w+)@", email):
                username = match.group(1)
            else:
                continue
            with (base_path / f"env-local-{username}-api.sh").open("w") as fp:
                print("# Directly access to the manager using API keypair (admin)", file=fp)
                print(
                    "export"
                    f" BACKEND_ENDPOINT=http://{service.manager_addr.face.host}:{service.manager_addr.face.port}/",
                    file=fp,
                )
                print("export BACKEND_ENDPOINT_TYPE=api", file=fp)
                print(f"export BACKEND_ACCESS_KEY={keypair['access_key']}", file=fp)
                print(f"export BACKEND_SECRET_KEY={keypair['secret_key']}", file=fp)
        with self.resource_path("ai.backend.install.fixtures", "example-users.json") as user_path:
            current_shell = os.environ.get("SHELL", "sh")
            user_data = json.loads(Path(user_path).read_bytes())
        for user in user_data["users"]:
            username = user["username"]
            with (base_path / f"env-local-{username}-session.sh").open("w") as fp:
                print(
                    "# Indirectly access to the manager via the web server using a cookie-based"
                    " login session",
                    file=fp,
                )
                print(
                    "export"
                    f" BACKEND_ENDPOINT=http://{service.webserver_addr.face.host}:{service.webserver_addr.face.port}/",
                    file=fp,
                )
                print("export BACKEND_ENDPOINT_TYPE=session", file=fp)
                if current_shell == "fish":
                    print("set -e BACKEND_ACCESS_KEY", file=fp)
                    print("set -e BACKEND_SECRET_KEY", file=fp)
                else:
                    print("unset BACKEND_ACCESS_KEY", file=fp)
                    print("unset BACKEND_SECRET_KEY", file=fp)
                client_executable = self.mangle_pkgname("client")
                print(
                    f"""echo 'Run `./{client_executable} login` to activate a login session.'""",
                    file=fp,
                )
                print(f"""echo 'Your email: {user["email"]}'""", file=fp)
                print(f"""echo 'Your password: {user["password"]}'""", file=fp)

    def _resolve_harbor_hostname(self, public_facing_address: str) -> str:
        """
        Pick a Harbor hostname that Harbor's ``prepare`` script will accept.

        Harbor explicitly rejects loopback addresses (``127.0.0.1`` /
        ``localhost``) and ``0.0.0.0``. When ``--public-facing-address`` is
        one of those (the dev-installer default is ``127.0.0.1``), fall back
        to ``host.docker.internal`` so Harbor still gets a reachable name on
        Docker Desktop / OrbStack hosts. Users can override the choice with
        ``--harbor-hostname``.
        """
        override = self.install_variable.harbor_hostname
        if override:
            return override
        if public_facing_address in ("127.0.0.1", "0.0.0.0", "localhost"):
            return "host.docker.internal"
        return public_facing_address

    async def configure_harbor(self) -> None:
        """
        Configure and install a local Harbor container registry.

        Downloads the Harbor offline installer archive, extracts it into
        ``<base_path>/harbor``, writes ``harbor.yml`` from the bundled template
        (replacing ``hostname``/``http port``/``admin password``/``data_volume``
        placeholders), and runs Harbor's own ``install.sh`` which in turn
        generates the working ``docker-compose.yml`` and config files for the
        core, portal, registry, jobservice, and database containers.

        The generated ``docker-compose.yml`` can then be managed with
        ``docker compose -f harbor/docker-compose.yml up -d`` or via the
        ``./dev harbor start/stop`` helpers.
        """
        service = self.install_info.service_config
        if not service.harbor_enabled:
            return

        base_path = self.install_info.base_path
        harbor_dir = base_path / "harbor"
        harbor_data_dir = base_path / "var" / "harbor"
        harbor_data_dir.mkdir(parents=True, exist_ok=True)

        if service.harbor_admin_password == "Harbor12345":
            self.log.write(
                Text.from_markup(
                    "[yellow]WARNING: using the well-known default Harbor admin "
                    "password 'Harbor12345'. Override with --harbor-admin-password "
                    "for anything beyond a throwaway dev box.[/]"
                )
            )

        # If a previous Harbor install has containers running, refusing to
        # re-prepare under them prevents desync between the on-disk compose
        # project and the running state (and avoids accidentally tearing
        # down a Harbor that this run did not start).
        if (
            harbor_dir / "docker-compose.yml"
        ).exists() and await self._harbor_compose_has_running_containers(harbor_dir):
            self.log.write(
                Text.from_markup(
                    "[yellow]Existing Harbor containers detected — leaving the "
                    "current installation in place. Run [bold]./dev harbor stop[/] "
                    "and re-run the installer to refresh the configuration.[/]"
                )
            )
            await self._register_local_harbor_registry()
            return

        download_uri = self.install_variable.harbor_download_uri
        expected_sha256 = self.install_variable.harbor_download_sha256
        archive_path = base_path / Path(download_uri).name

        # 1) Download the Harbor offline installer archive if not already present.
        if not archive_path.exists():
            self.log_header(f"Downloading Harbor offline installer from {download_uri}")
            exit_code = await self.run_exec(
                ["curl", "-fL", "--output", str(archive_path), download_uri],
                cwd=base_path,
            )
            if exit_code != 0:
                raise RuntimeError(
                    f"Harbor download failed (curl exit {exit_code}); URL: {download_uri}"
                )
        else:
            self.log.write(
                Text.from_markup(
                    f"Using cached Harbor installer archive at [bold]{archive_path}[/]"
                )
            )

        # 2) Verify the archive against a pinned SHA-256 when one is configured.
        #    Upstream Harbor publishes only MD5 sums, so the digest must be
        #    provided by the operator (--harbor-download-sha256). When unset
        #    we skip the check and surface a one-line warning rather than
        #    silently trusting the download.
        if expected_sha256:
            self.log_header("Verifying Harbor archive SHA-256...")
            actual_sha256 = await self._sha256_file(archive_path)
            if actual_sha256.lower() != expected_sha256.lower():
                raise RuntimeError(
                    f"Harbor archive SHA-256 mismatch: expected {expected_sha256}, "
                    f"got {actual_sha256}. Refusing to extract a potentially "
                    f"tampered archive at {archive_path}."
                )
            self.log.write(Text.from_markup(f"[green]SHA-256 OK[/] [dim]({actual_sha256})[/]"))
        else:
            self.log.write(
                Text.from_markup(
                    "[yellow]No --harbor-download-sha256 supplied; skipping "
                    "archive integrity check. Pass an expected digest to enable "
                    "verification.[/]"
                )
            )

        # 3) Replace the installer directory atomically so that scripts/configs
        #    from a previous (possibly different-version) archive do not linger.
        #    data_volume lives at <base_path>/var/harbor and is outside
        #    harbor_dir, so wiping harbor_dir does not touch persistent data.
        if harbor_dir.exists():
            shutil.rmtree(harbor_dir)
        harbor_dir.mkdir(parents=True, exist_ok=True)

        self.log_header("Extracting Harbor installer archive...")
        with tempfile.TemporaryDirectory(prefix="bai-harbor-") as extract_root:
            extract_path = Path(extract_root)
            exit_code = await self.run_exec(
                ["tar", "-xzf", str(archive_path), "-C", str(extract_path)],
                cwd=base_path,
            )
            if exit_code != 0:
                raise RuntimeError(
                    f"Harbor archive extraction failed (tar exit {exit_code}); archive may be corrupt: {archive_path}"
                )
            # The tarball extracts into a top-level ``harbor/`` directory.
            extracted_harbor_dir = extract_path / "harbor"
            if not extracted_harbor_dir.is_dir():
                raise RuntimeError(
                    f"Harbor archive did not contain a top-level 'harbor/' directory: {archive_path}"
                )
            for child in extracted_harbor_dir.iterdir():
                dest = harbor_dir / child.name
                if child.is_dir():
                    shutil.copytree(child, dest)
                else:
                    shutil.copy2(child, dest)

        # 4) Load Harbor's bundled ``harbor.yml.tmpl`` using ruamel.yaml
        #    (round-trip mode) so we can modify only the fields we care about
        #    while preserving comments and structure — mirroring the tomlkit
        #    pattern used for other service configs.
        self.log_header("Writing harbor.yml configuration...")
        harbor_template = harbor_dir / "harbor.yml.tmpl"
        if not harbor_template.exists():
            raise RuntimeError(
                f"Harbor template not found at {harbor_template}; archive may be corrupt."
            )
        yaml = YAML()
        yaml.preserve_quotes = True
        with harbor_template.open("r", encoding="utf-8") as fp:
            harbor_config = yaml.load(fp)
        harbor_config["hostname"] = service.harbor_hostname
        harbor_config["http"]["port"] = service.harbor_http_port
        harbor_config["harbor_admin_password"] = service.harbor_admin_password
        harbor_config["database"]["password"] = service.harbor_admin_password
        harbor_config["data_volume"] = str(harbor_data_dir)
        # Drop the https section entirely so that ``prepare`` does not require
        # certificate files. The template keeps it commented out by default,
        # but be defensive in case a newer archive enables it.
        if "https" in harbor_config:
            del harbor_config["https"]
        with (harbor_dir / "harbor.yml").open("w", encoding="utf-8") as fp:
            yaml.dump(harbor_config, fp)

        # 5) Load the bundled service images (``harbor.<version>.tar.gz``)
        #    so the prepare container — and any later ``./dev harbor start`` —
        #    can run without an internet round-trip.
        image_tarballs = sorted(harbor_dir.glob("harbor.*.tar.gz"))
        if image_tarballs:
            self.log_header("Loading bundled Harbor images into docker...")
            for image_tarball in image_tarballs:
                exit_code = await self.run_exec(
                    [*self.docker_sudo, "docker", "load", "-i", str(image_tarball)],
                    cwd=harbor_dir,
                )
                if exit_code != 0:
                    raise RuntimeError(
                        f"docker load failed for {image_tarball.name} (exit {exit_code})."
                    )

        # 6) Run Harbor's ``prepare`` script directly to generate
        #    docker-compose.yml and supporting service configs. We deliberately
        #    avoid ``install.sh`` because it also runs ``docker compose up`` —
        #    we manage Harbor's lifecycle via ``./dev harbor start|stop``, and
        #    bringing containers up here would force a ``docker compose down``
        #    that could tear down a Harbor someone else started.
        self.log_header("Running Harbor prepare script...")
        prepare_script = harbor_dir / "prepare"
        if not prepare_script.exists():
            raise RuntimeError(
                f"Harbor prepare script not found at {prepare_script}; archive may be corrupt."
            )
        exit_code = await self.run_exec(
            ["bash", "prepare"],
            cwd=harbor_dir,
        )
        if exit_code != 0:
            raise RuntimeError(
                f"Harbor prepare failed (exit {exit_code}); check the log above for details."
            )

        # 7) Register the local Harbor as a Backend.AI container registry so
        #    images can be scanned/pulled from it without an extra manual step.
        await self._register_local_harbor_registry()

        self.log.write(
            Text.from_markup(
                f"[green]Harbor is configured.[/] "
                f"Start it with [bold]./dev harbor start[/] and access it at "
                f"[bold]http://{service.harbor_hostname}:{service.harbor_http_port}[/]"
            )
        )

    async def _harbor_compose_has_running_containers(self, harbor_dir: Path) -> bool:
        """Return True if ``docker compose ps -q`` in ``harbor_dir`` lists any
        container IDs. Used to detect a previously-installed Harbor that is
        currently up, so the installer can refuse to re-prepare under it."""
        proc = await asyncio.create_subprocess_exec(
            *self.docker_sudo,
            "docker",
            "compose",
            "ps",
            "-q",
            cwd=str(harbor_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return proc.returncode == 0 and bool(stdout.strip())

    @staticmethod
    async def _sha256_file(path: Path) -> str:
        """Compute the SHA-256 of ``path`` off the event loop."""

        def _digest() -> str:
            h = hashlib.sha256()
            with path.open("rb") as fp:
                for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()

        return await asyncio.to_thread(_digest)

    async def _register_local_harbor_registry(self) -> None:
        """
        Register the freshly configured local Harbor as a Backend.AI
        ``container_registries`` row (with admin credentials) so it shows up
        immediately in the manager API/UI without manual registration.

        The fixture uses ``uuid5(NAMESPACE_URL, harbor_url)`` for the row ID
        so re-running the installer does not create duplicate rows — the
        manager's fixture loader treats a matching primary key as
        idempotent.
        """
        service = self.install_info.service_config
        harbor_url = f"http://{service.harbor_hostname}:{service.harbor_http_port}"
        registry_name = "local-harbor"
        project = "library"
        registry_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{harbor_url}/{project}"))
        fixture = {
            "container_registries": [
                {
                    "id": registry_id,
                    "registry_name": registry_name,
                    "url": harbor_url,
                    "type": "harbor2",
                    "project": project,
                    "username": "admin",
                    "password": service.harbor_admin_password,
                    "ssl_verify": False,
                }
            ]
        }
        fixture_path = self.install_info.base_path / "harbor" / "container-registry-fixture.json"
        fixture_path.write_text(json.dumps(fixture, indent=2))
        self.log_header("Registering local Harbor as a Backend.AI container registry...")
        await self.run_manager_cli(["mgr", "fixture", "populate", str(fixture_path)])

    async def dump_install_info(self) -> None:
        self.log_header("Dumping the installation configs...")
        base_path = self.install_info.base_path
        etcd_dump = dict(await self.etcd_get_json(""))  # conv chainmap to normal dict
        etcd_dump_path = base_path / "etcd.installed.json"
        etcd_dump_path.write_text(json.dumps(etcd_dump))
        self.log.write(
            Text.from_markup(f"stored the etcd configuration as [bold]{etcd_dump_path}[/]")
        )
        install_info_path = Path.cwd() / "INSTALL-INFO"
        install_info_path.write_text(self.install_info.model_dump_json())
        self.log.write(
            Text.from_markup(f"stored the installation info as [bold]{install_info_path}[/]")
        )

    async def get_db_connection(self) -> asyncpg.Connection:
        halfstack = self.install_info.halfstack_config
        return await asyncpg.connect(
            host=halfstack.postgres_addr.face.host,
            port=halfstack.postgres_addr.face.port,
            user=halfstack.postgres_user,
            password=halfstack.postgres_password,
            database="backend",
        )

    async def prepare_local_vfolder_host(self) -> None:
        service = self.install_info.service_config
        volume_root = Path(self.install_info.base_path / service.vfolder_relpath)
        volume_root.mkdir(parents=True, exist_ok=True)
        await asyncio.sleep(0)
        Path(volume_root / "version.txt").write_text("3")
        scratch_root = Path(self.install_info.base_path / "scratches")
        scratch_root.mkdir(parents=True, exist_ok=True)
        await asyncio.sleep(0)
        async with aiotools.closing_async(await self.get_db_connection()) as conn:
            default_vfolder_host_perms = [
                "create-vfolder",
                "modify-vfolder",
                "delete-vfolder",
                "mount-in-session",
                "upload-file",
                "download-file",
                "invite-others",
                "set-user-specific-permission",
            ]
            update_arg = json.dumps({"local:volume1": default_vfolder_host_perms})
            await conn.execute(
                "UPDATE domains SET allowed_vfolder_hosts = $1::jsonb;",
                update_arg,
            )
            await conn.execute(
                "UPDATE groups SET allowed_vfolder_hosts = $1::jsonb;",
                update_arg,
            )
            await conn.execute(
                "UPDATE keypair_resource_policies SET allowed_vfolder_hosts = $1::jsonb;",
                update_arg,
            )
            await conn.execute(
                "UPDATE vfolders SET host = $1;",
                "local:volume1",
            )

    async def alias_image(self, alias: str, target_ref: str, arch: str) -> None:
        await self.run_manager_cli([
            "mgr",
            "image",
            "alias",
            alias,
            target_ref,
            arch,
        ])

    async def populate_images(self) -> None:
        data: Any
        for image_source in self.dist_info.image_sources:
            match image_source:
                case ImageSource.BACKENDAI_REGISTRY:
                    self.log_header(
                        "Scanning and pulling configured Backend.AI container images..."
                    )

                    data = {
                        "docker": {
                            "image": {
                                "auto_pull": "tag",
                            },
                        },
                    }
                    await self.etcd_put_json("config", data)

                    await self.run_manager_cli(["mgr", "image", "rescan", "cr.backend.ai"])
                    if self.os_info.platform in (Platform.LINUX_ARM64, Platform.MACOS_ARM64):
                        await self.alias_image(
                            "python",
                            "cr.backend.ai/stable/python:3.13-ubuntu24.04-arm64",
                            "aarch64",
                        )
                    else:
                        await self.alias_image(
                            "python",
                            "cr.backend.ai/stable/python:3.13-ubuntu24.04-amd64",
                            "x86_64",
                        )

                    if self.install_info.service_config.sftp_agent_enabled:
                        # Pre-pull the SFTP server image so the first SFTP
                        # session does not stall on a cold image fetch. The
                        # tag is single-arch (multi-arch manifest); the
                        # registered metadata also makes it resolvable for
                        # storage-proxy when routing SFTP upload sessions.
                        sftp_image_ref = "cr.backend.ai/stable/sftp-server:24.04-ubuntu24.04"
                        await self.run_exec([
                            *self.docker_sudo,
                            "docker",
                            "pull",
                            sftp_image_ref,
                        ])
                case ImageSource.DOCKER_HUB:
                    self.log_header(
                        "Scanning and pulling configured Docker Hub container images..."
                    )
                    data = {
                        "docker": {
                            "image": {
                                "auto_pull": "tag",
                            },
                        },
                    }
                    await self.etcd_put_json("config", data)

                    for ref in self.dist_info.image_refs:
                        await self.run_manager_cli(["mgr", "image", "rescan", ref])
                        await self.run_exec([*self.docker_sudo, "docker", "pull", ref])
                case ImageSource.LOCAL_DIR:
                    self.log_header("Populating local container images...")
                    for src in self.dist_info.image_payloads:
                        # TODO: Ensure src.ref
                        await self.run_exec([
                            *self.docker_sudo,
                            "docker",
                            "load",
                            "-i",
                            str(src.file),
                        ])
                case ImageSource.LOCAL_REGISTRY:
                    raise NotImplementedError


class DevContext(Context):
    def hydrate_install_info(self) -> InstallInfo:
        # TODO: customize addr/user/password options
        # TODO: multi-node setup
        public_facing_address = self.install_variable.public_facing_address
        if public_facing_address in ("127.0.0.1", "localhost"):
            public_component_bind_address = "127.0.0.1"
        else:
            public_component_bind_address = "0.0.0.0"
        halfstack_config = HalfstackConfig(
            ha_setup=False,
            postgres_addr=ServerAddr(HostPortPair("127.0.0.1", 8100)),
            postgres_user="postgres",
            postgres_password="develove",
            redis_addr=ServerAddr(HostPortPair("127.0.0.1", 8110)),
            redis_sentinel_addrs=[],
            redis_password=None,
            etcd_addr=[ServerAddr(HostPortPair("127.0.0.1", 8120))],
            etcd_user=None,
            etcd_password=None,
        )
        service_config = ServiceConfig(
            webserver_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 8090),
                face=HostPortPair(public_facing_address, 8090),
            ),
            webserver_ipc_base_path="ipc/webserver",
            webserver_var_base_path="var/webserver",
            webui_menu_blocklist=["pipeline"],
            webui_menu_inactivelist=["statistics"],
            manager_addr=ServerAddr(HostPortPair("127.0.0.1", 8091)),
            storage_proxy_manager_auth_key=secrets.token_hex(32),
            manager_ipc_base_path="ipc/manager",
            manager_var_base_path="var/manager",
            local_proxy_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 5050),
                face=HostPortPair(public_facing_address, 5050),
            ),
            scaling_group="default",
            agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6011)),
            agent_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6019)),
            agent_sock_port=6007,
            agent_ipc_base_path="ipc/agent",
            agent_var_base_path="var/agent",
            storage_proxy_client_facing_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 6021),
                face=HostPortPair(public_facing_address, 6021),
            ),
            storage_proxy_manager_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6022)),
            storage_proxy_ipc_base_path="ipc/storage-proxy",
            storage_proxy_var_base_path="var/storage-proxy",
            storage_proxy_random=secrets.token_hex(32),
            storage_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6029)),
            storage_agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6012)),
            storage_agent_ipc_base_path="ipc/storage-agent",
            storage_agent_var_base_path="var/storage-agent",
            vfolder_relpath="vfolder/local/volume1",
            appproxy_api_secret=secrets.token_hex(32),
            appproxy_jwt_secret=secrets.token_hex(32),
            appproxy_permit_hash_secret=secrets.token_hex(32),
            appproxy_coordinator_addr=ServerAddr(HostPortPair(public_facing_address, 10200)),
            appproxy_worker_addr=ServerAddr(HostPortPair(public_facing_address, 10201)),
            appproxy_tcp_worker_addr=ServerAddr(HostPortPair(public_facing_address, 10202)),
            harbor_enabled=self.install_variable.with_harbor,
            harbor_hostname=self._resolve_harbor_hostname(public_facing_address),
            harbor_http_port=self.install_variable.harbor_http_port,
            harbor_admin_password=self.install_variable.harbor_admin_password,
            sftp_agent_enabled=self.install_variable.with_sftp_agent,
            sftp_agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6013)),
            sftp_agent_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6015)),
            sftp_agent_var_base_path="var/agent-sftp",
            sftp_agent_scaling_group="upload",
        )

        return InstallInfo(
            version=self.dist_info.version,
            base_path=Path.cwd(),
            type=InstallType.SOURCE,
            last_updated=datetime.now(tzutc()),
            halfstack_config=halfstack_config,
            service_config=service_config,
            accelerator=self.install_variable.accelerator,
        )

    def copy_config(self, template_name: str) -> Path:
        with self.resource_path("ai.backend.install.configs", template_name) as src_path:
            dst_path = Path.cwd() / template_name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy(src_path, dst_path)
        return dst_path

    async def check_prerequisites(self) -> None:
        await super().check_prerequisites()
        await install_git_lfs(self)
        await install_git_hooks(self)
        await check_python(self)
        local_execution_root_dir = await get_preferred_pants_local_exec_root(self)
        await bootstrap_pants(self, local_execution_root_dir)

    async def install(self) -> None:
        await pants_export(self)
        await install_editable_webui(self)
        await self.install_halfstack()

    async def _configure_mock_accelerator(self, accelerator: Accelerator) -> None:
        """
        cp "configs/accelerator/mock-accelerator.toml" mock-accelerator.toml
        """
        mapping = {
            Accelerator.CUDA_MOCK: "configs/accelerator/mock-accelerator.toml",
            Accelerator.CUDA_MIG_MOCK: "configs/accelerator/cuda-mock-mig.toml",
            Accelerator.ROCM_MOCK: "configs/accelerator/rocm-mock.toml",
        }

        src = mapping.get(accelerator)
        if not src:
            return

        dst = Path("mock-accelerator.toml")
        print(f"[Installer] Copying accelerator config: {src} -> {dst}")
        shutil.copy(src, dst)

    async def configure(self) -> None:
        self.log_header("Configuring manager...")
        await self.configure_manager()

        # Manager schema must exist before updating scaling_groups
        self.log_header("Initializing manager database schema...")
        await self.run_manager_cli(["mgr", "schema", "oneshot"])

        self.log_header("Configuring agent...")
        await self.configure_agent()

        if self.install_variable.with_sftp_agent:
            self.log_header("Configuring dedicated SFTP agent...")
            await self.configure_sftp_agent()

        self.log_header("Initializing app-proxy database...")
        await self.install_appproxy_db()

        self.log_header("Configuring storage-proxy...")
        await self.configure_storage_proxy()

        self.log_header("Configuring webserver and webui...")
        await self.configure_webserver()
        await self.configure_webui()

        self.log_header("Loading fixtures...")
        await self.load_fixtures()

        self.log_header("Configuring app-proxy...")
        await self.configure_appproxy()
        await self.configure_appproxy_fixture()

        if self.install_variable.with_sftp_agent:
            await self.configure_sftp_agent_fixture()

        self.log_header("Generating client environ configs...")
        await self.configure_client()

        if self.install_variable.with_harbor:
            self.log_header("Configuring local Harbor registry...")
            await self.configure_harbor()

        self.log_header("Preparing vfolder volumes...")
        await self.prepare_local_vfolder_host()


class PackageContext(Context):
    def hydrate_install_info(self) -> InstallInfo:
        # TODO: customize addr/user/password options
        # TODO: multi-node setup
        public_facing_address = self.install_variable.public_facing_address
        if public_facing_address in ("127.0.0.1", "0.0.0.0"):
            public_component_bind_address = "127.0.0.1"
        else:
            public_component_bind_address = "0.0.0.0"
        halfstack_config = HalfstackConfig(
            ha_setup=False,
            postgres_addr=ServerAddr(HostPortPair("127.0.0.1", 8100)),
            postgres_user="postgres",
            postgres_password="develove",
            redis_addr=ServerAddr(HostPortPair("127.0.0.1", 8110)),
            redis_sentinel_addrs=[],
            redis_password=None,
            etcd_addr=[ServerAddr(HostPortPair("127.0.0.1", 8120))],
            etcd_user=None,
            etcd_password=None,
        )
        service_config = ServiceConfig(
            webserver_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 8090),
                face=HostPortPair(public_facing_address, 8090),
            ),
            webserver_ipc_base_path="ipc/webserver",
            webserver_var_base_path="var/webserver",
            webui_menu_blocklist=["pipeline"],
            webui_menu_inactivelist=["statistics"],
            manager_addr=ServerAddr(HostPortPair("127.0.0.1", 8091)),
            storage_proxy_manager_auth_key=secrets.token_urlsafe(32),
            manager_ipc_base_path="ipc/manager",
            manager_var_base_path="var/manager",
            local_proxy_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 15050),
                face=HostPortPair(public_facing_address, 15050),
            ),
            scaling_group="default",
            agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6011)),
            agent_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6019)),
            agent_sock_port=6007,
            agent_ipc_base_path="ipc/agent",
            agent_var_base_path="var/agent",
            storage_proxy_client_facing_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 6021),
                face=HostPortPair(public_facing_address, 6021),
            ),
            storage_proxy_manager_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6022)),
            storage_proxy_ipc_base_path="ipc/storage-proxy",
            storage_proxy_var_base_path="var/storage-proxy",
            storage_proxy_random=secrets.token_urlsafe(32),
            storage_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6029)),
            storage_agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6012)),
            storage_agent_ipc_base_path="ipc/storage-agent",
            storage_agent_var_base_path="var/storage-agent",
            vfolder_relpath="vfolder/local/volume1",
            appproxy_api_secret=secrets.token_hex(32),
            appproxy_jwt_secret=secrets.token_hex(32),
            appproxy_permit_hash_secret=secrets.token_hex(32),
            appproxy_coordinator_addr=ServerAddr(HostPortPair(public_facing_address, 10200)),
            appproxy_worker_addr=ServerAddr(HostPortPair(public_facing_address, 10201)),
            appproxy_tcp_worker_addr=ServerAddr(HostPortPair(public_facing_address, 10202)),
        )
        return InstallInfo(
            version=self.dist_info.version,
            base_path=self.dist_info.target_path,
            type=InstallType.PACKAGE,
            last_updated=datetime.now(tzutc()),
            halfstack_config=halfstack_config,
            service_config=service_config,
            accelerator=self.install_variable.accelerator,
        )

    def copy_config(self, template_name: str) -> Path:
        with self.resource_path("ai.backend.install.configs", template_name) as src_path:
            dst_path = self.dist_info.target_path / template_name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy(src_path, dst_path)
        return dst_path

    async def check_prerequisites(self) -> None:
        await super().check_prerequisites()
        if self.install_variable.with_harbor:
            raise PrerequisiteError(
                "--with-harbor is supported only in DEVELOP/SOURCE install modes; "
                "package mode does not provision a local Harbor registry."
            )

    async def _validate_checksum(self, pkg_path: Path, csum_path: Path) -> None:
        proc = await asyncio.create_subprocess_exec(
            *["shasum", "-a", "256", "-c", csum_path.name],
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            cwd=csum_path.parent,
        )
        exit_code = await proc.wait()
        if exit_code == 0:
            return
        raise RuntimeError(
            f"Failed to validate the checksum of {pkg_path}. "
            "Please check the install media and retry after removing it."
        )

    async def _fetch_package(self, name: str, vpane: Vertical) -> None:
        pkg_name = self.mangle_pkgname(name)
        dst_path = self.dist_info.target_path / pkg_name
        pkg_url = f"https://github.com/lablup/backend.ai/releases/download/{self.dist_info.version}/{pkg_name}"
        self.log.write(f"Downloading {pkg_url}...")
        item = ProgressItem(f"[blue](download)[/] {pkg_name}")
        await vpane.mount(item)
        progress = item.get_child_by_type(ProgressBar)
        async with self.wget_sema:
            await wget(pkg_url, dst_path, progress)

    async def _fetch_checksums(self, vpane: Vertical) -> None:
        csum_url = f"https://github.com/lablup/backend.ai/releases/download/{self.dist_info.version}/checksum.txt"
        dst_path = self.dist_info.target_path / "checksum.txt"
        self.log.write(f"Downloading {csum_url}...")
        item = ProgressItem("[blue](download)[/] checksum.txt")
        await vpane.mount(item)
        progress = item.get_child_by_type(ProgressBar)
        async with self.wget_sema:
            await wget(csum_url, dst_path, progress)

    async def _verify_package(self, name: str, *, fat: bool) -> None:
        pkg_name = self.mangle_pkgname(name, fat=fat)
        dst_path = self.dist_info.target_path / pkg_name
        self.log.write(f"Verifying {dst_path} ...")
        csum_path = self.dist_info.target_path / "checksum.txt"

        csum_line: str = ""
        with csum_path.open() as f:
            lines = f.readlines()
            for line in lines:
                if pkg_name in line:
                    csum_line = line
                    break
            else:
                raise ValueError(f"Checksum for {pkg_name} not found in {csum_path}")

        individual_csum_path = dst_path.with_name(pkg_name + ".sha256")
        with individual_csum_path.open("w") as f:
            f.write(csum_line)

        await self._validate_checksum(dst_path, individual_csum_path)
        individual_csum_path.unlink()
        dst_path.chmod(0o755)
        dst_path.rename(dst_path.with_name(f"backendai-{name}"))

    async def _install_package(self, name: str, vpane: Vertical, *, fat: bool) -> None:
        self.dist_info.target_path.mkdir(parents=True, exist_ok=True)
        pkg_name = self.mangle_pkgname(name, fat=fat)
        src_path = self.dist_info.package_dir / pkg_name
        dst_path = self.dist_info.target_path / pkg_name
        item = ProgressItem(f"[blue](install)[/] {pkg_name}")
        await vpane.mount(item)
        progress = item.get_child_by_type(ProgressBar)
        progress.update(total=src_path.stat().st_size)
        async with (
            aiofiles.open(src_path, "rb") as src,
            aiofiles.open(dst_path, "wb") as dst,
        ):
            while True:
                chunk = await src.read(1048576)
                if not chunk:
                    break
                await dst.write(chunk)
                progress.advance(len(chunk))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            partial(
                shutil.copy,
                src_path.with_name(pkg_name + ".sha256"),
                dst_path.with_name(pkg_name + ".sha256"),
            ),
        )

    async def install(self) -> None:
        vpane = Vertical(id="download-status")
        await self.log.mount(vpane)
        try:
            match self.dist_info.package_source:
                case PackageSource.GITHUB_RELEASE:
                    # Download (NOTE: we always use the lazy version here)
                    # In this case, we download the packages directly into the target path.
                    self.log_header(
                        f"Downloading prebuilt packages into {self.dist_info.target_path}..."
                    )
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self._fetch_package("manager", vpane))
                        tg.create_task(self._fetch_package("agent", vpane))
                        tg.create_task(self._fetch_package("agent-watcher", vpane))
                        tg.create_task(self._fetch_package("webserver", vpane))
                        tg.create_task(self._fetch_package("appproxy-coordinator", vpane))
                        tg.create_task(self._fetch_package("appproxy-worker", vpane))
                        tg.create_task(self._fetch_package("storage-proxy", vpane))
                        tg.create_task(self._fetch_package("client", vpane))
                        tg.create_task(self._fetch_checksums(vpane))
                    # Verify the checksums of the downloaded packages.
                    await self._verify_package("manager", fat=False)
                    await self._verify_package("agent", fat=False)
                    await self._verify_package("agent-watcher", fat=False)
                    await self._verify_package("webserver", fat=False)
                    await self._verify_package("appproxy-coordinator", fat=False)
                    await self._verify_package("appproxy-worker", fat=False)
                    await self._verify_package("storage-proxy", fat=False)
                    await self._verify_package("client", fat=False)
                case PackageSource.LOCAL_DIR:
                    # Use the local files.
                    # Copy the packages into the target path.
                    self.log_header(f"Installing packages into {self.dist_info.target_path}...")
                    await self._install_package("manager", vpane, fat=self.dist_info.use_fat_binary)
                    await self._install_package("agent", vpane, fat=self.dist_info.use_fat_binary)
                    await self._install_package(
                        "agent-watcher", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package(
                        "webserver", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package(
                        "appproxy-coordinator", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package(
                        "appproxy-worker", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package(
                        "storage-proxy", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package("client", vpane, fat=self.dist_info.use_fat_binary)
                    # Verify the checksums.
                    await self._verify_package("manager", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("agent", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("agent-watcher", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("webserver", fat=self.dist_info.use_fat_binary)
                    await self._verify_package(
                        "appproxy-coordinator", fat=self.dist_info.use_fat_binary
                    )
                    await self._verify_package("appproxy-worker", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("storage-proxy", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("client", fat=self.dist_info.use_fat_binary)
        finally:
            vpane.remove()
        self.log_header("Installing databases (halfstack)...")
        await self.install_halfstack()

    async def _configure_mock_accelerator(self, accelerator: Accelerator) -> None:
        """
        cp "configs/accelerator/mock-accelerator.toml" mock-accelerator.toml
        """
        mapping = {
            Accelerator.CUDA_MOCK: "configs/accelerator/mock-accelerator.toml",
            Accelerator.CUDA_MIG_MOCK: "configs/accelerator/cuda-mock-mig.toml",
            Accelerator.ROCM_MOCK: "configs/accelerator/rocm-mock.toml",
        }

        src = mapping.get(accelerator)
        if not src:
            return

        dst = Path("mock-accelerator.toml")
        print(f"[Installer] Copying accelerator config: {src} -> {dst}")
        shutil.copy(src, dst)

    async def configure(self) -> None:
        self.log_header("Configuring manager...")
        await self.configure_manager()

        # Manager schema must exist before fixtures and the app-proxy DB step
        # update scaling_groups (mirrors the DevContext.configure() order).
        self.log_header("Initializing manager database schema...")
        await self.run_manager_cli(["mgr", "schema", "oneshot"])

        self.log_header("Configuring agent...")
        await self.configure_agent()
        self.log_header("Configuring storage-proxy...")
        await self.configure_storage_proxy()
        self.log_header("Configuring webserver and webui...")
        await self.configure_webserver()
        await self.configure_webui()
        self.log_header("Configuring app-proxy...")
        await self.install_appproxy_db()
        await self.configure_appproxy()
        self.log_header("Generating client environ configs...")
        await self.configure_client()
        self.log_header("Loading fixtures...")
        await self.load_fixtures()
        self.log_header("Preparing vfolder volumes...")
        await self.prepare_local_vfolder_host()
        # TODO: install as systemd services?
