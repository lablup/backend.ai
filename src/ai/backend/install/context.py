from __future__ import annotations

import asyncio
import enum
import json
import re
import secrets
import shutil
from abc import ABCMeta, abstractmethod
from contextlib import aclosing
from contextvars import ContextVar
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, Sequence

import aiofiles
import asyncpg
import pkg_resources
from dateutil.tz import tzutc
from rich.text import Text
from textual.app import App
from textual.containers import Vertical
from textual.widgets import Label, ProgressBar, RichLog, Static

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes

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
from .types import (
    DistInfo,
    HalfstackConfig,
    HostPortPair,
    InstallInfo,
    InstallType,
    OSInfo,
    PackageSource,
    Platform,
    ServerAddr,
    ServiceConfig,
)

current_log: ContextVar[RichLog] = ContextVar("current_log")


class PostGuide(enum.Enum):
    UPDATE_ETC_HOSTS = 10


class Context(metaclass=ABCMeta):
    os_info: OSInfo

    _post_guides: list[PostGuide]

    def __init__(self, dist_info: DistInfo, app: App) -> None:
        self._post_guides = []
        self.app = app
        self.log = current_log.get()
        self.cwd = Path.cwd()
        self.dist_info = dist_info
        self.wget_sema = asyncio.Semaphore(3)
        self.install_info = self.hydrate_install_info()

    @abstractmethod
    def hydrate_install_info(self) -> InstallInfo:
        raise NotImplementedError

    def add_post_guide(self, guide: PostGuide) -> None:
        self._post_guides.append(guide)

    def show_post_guide(self) -> None:
        pass

    def log_header(self, title: str) -> None:
        self.log.write(Text.from_markup(f"[bright_green]:green_circle: {title}"))

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

    async def run_exec(self, cmdargs: Sequence[str], **kwargs) -> int:
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
                exit_code = await p.wait()
            except asyncio.TimeoutError:
                p.kill()
                exit_code = await p.wait()
        return exit_code

    async def run_shell(self, script: str, **kwargs) -> int:
        return await self.run_exec(["sh", "-c", script], **kwargs)

    def copy_config(self, template_name: str) -> Path:
        src_path = pkg_resources.resource_filename("ai.backend.install.configs", template_name)
        dst_path = self.dist_info.target_path / template_name
        shutil.copy(src_path, dst_path)
        return dst_path

    @staticmethod
    def sed_in_place(path: Path, pattern: str | re.Pattern, replacement: str) -> None:
        content = path.read_text()
        match pattern:
            case str():
                content = content.replace(pattern, replacement)
            case re.Pattern():
                content = pattern.sub(replacement, content)
        path.write_text(content)

    @staticmethod
    def sed_in_place_multi(path: Path, subs: Sequence[tuple[str | re.Pattern, str]]) -> None:
        content = path.read_text()
        for pattern, replacement in subs:
            match pattern:
                case str():
                    content = content.replace(pattern, replacement)
                case re.Pattern():
                    content = pattern.sub(replacement, content)
        path.write_text(content)

    async def run_manager_cli(self, cmdargs: Sequence[str]) -> None:
        executable = Path(self.install_info.base_path) / "backendai-manager"
        await self.run_exec(
            [str(executable), *cmdargs],
            cwd=self.install_info.base_path,
        )

    async def put_etcd_json(self, key: str, value: Any) -> None:
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
        }
        halfstack = self.install_info.halfstack_config
        creds: dict[str, str] | None = None
        if halfstack.etcd_user is not None:
            assert halfstack.etcd_password is not None
            creds = {
                "user": halfstack.etcd_user,
                "password": halfstack.etcd_password,
            }
        etcd = AsyncEtcd(
            self.install_info.halfstack_config.etcd_addr[0].face,
            "local",
            scope_prefix_map,
            credentials=creds,
        )
        try:
            await etcd.put_prefix(key, value, scope=ConfigScopes.GLOBAL)
        finally:
            await etcd.close()

    async def install_halfstack(self) -> None:
        dst_compose_path = self.copy_config("docker-compose.yml")

        volume_path = self.install_info.base_path / "volumes"
        (volume_path / "postgres-data").mkdir(parents=True, exist_ok=True)
        (volume_path / "etcd-data").mkdir(parents=True, exist_ok=True)
        (volume_path / "redis-data").mkdir(parents=True, exist_ok=True)

        # TODO: implement ha setup
        assert self.install_info.halfstack_config.redis_addr
        self.sed_in_place_multi(
            dst_compose_path,
            [
                ("8100:5432", f"{self.install_info.halfstack_config.postgres_addr.bind.port}:5432"),
                ("8100:6379", f"{self.install_info.halfstack_config.redis_addr.bind.port}:6379"),
                ("8100:2379", f"{self.install_info.halfstack_config.etcd_addr[0].bind.port}:2379"),
            ],
        )
        await self.run_shell(
            """
        sudo docker compose pull && \\
        sudo docker compose up -d && \\
        sudo docker compose ps
        """,
            cwd=self.install_info.base_path,
        )

    async def load_fixtures(self) -> None:
        await self.run_manager_cli(["mgr", "schema", "oneshot"])
        await self.run_manager_cli(
            ["mgr", "fixture", "populate", "fixtures/manager/example-keypairs.json"]
        )
        await self.run_manager_cli(
            ["mgr", "fixture", "populate", "fixtures/manager/example-resource-presets.json"]
        )
        await self.run_manager_cli(["mgr", "image", "rescan", "cr.backend.ai"])

    async def configure_manager(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        toml_path = self.copy_config("manager.toml")
        alembic_path = self.copy_config("alembic.ini")
        self.sed_in_place_multi(
            toml_path,
            [
                (re.compile("^num-proc = .*"), "num-proc = 1"),
                ("port = 8120", f"port = {halfstack.etcd_addr[0].face.port}"),
                ("port = 8100", f"port = {halfstack.postgres_addr.face.port}"),
                (
                    "port = 8081",
                    f"port = {self.install_info.service_config.manager_addr.bind.port}",
                ),
                (
                    re.compile("^(# )?ipc-base-path =.*"),
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
                        "secret": self.install_info.service_config.manager_auth_key,
                        "ssl_verify": "false",
                    }
                },
                "exposed_volume_info": "percentage",
            },
        }
        await self.put_etcd_json("", data)
        data = {}
        if self.install_info.halfstack_config.ha_setup:
            assert self.install_info.halfstack_config.redis_sentinel_addrs
            data["redis"] = {
                "sentinel": ",".join(
                    f"{binding.host}:{binding.port}"
                    for binding in self.install_info.halfstack_config.redis_sentinel_addrs
                ),
                "service_name": "mymaster",
                "password": self.install_info.halfstack_config.redis_password,
                "helper": {
                    "socket_timeout": 5.0,
                    "socket_connect_timeout": 2.0,
                    "reconnect_poll_timeout": 0.3,
                },
            }
        else:
            assert self.install_info.halfstack_config.redis_addr
            data["redis"] = {
                "addr": f"{self.install_info.halfstack_config.redis_addr.face.host}:{self.install_info.halfstack_config.redis_addr.face.port}",
                "password": self.install_info.halfstack_config.redis_password,
                "helper": {
                    "socket_timeout": 5.0,
                    "socket_connect_timeout": 2.0,
                    "reconnect_poll_timeout": 0.3,
                },
            }
        (self.install_info.base_path / "etcd.config.json").write_text(json.dumps(data))
        await self.put_etcd_json("config", data)

    async def configure_agent(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        toml_path = self.copy_config("agent.toml")
        self.sed_in_place_multi(
            toml_path,
            [
                ("port = 8120", f"port = {halfstack.etcd_addr[0].face.port}"),
                ("port = 6001", f"port = {service.agent_rpc_addr.bind.port}"),
                ("port = 6009", f"port = {service.agent_watcher_addr.bind.port}"),
                (
                    re.compile("^(# )?ipc-base-path = .*"),
                    f'ipc-base-path = "{service.agent_ipc_base_path}"',
                ),
                (
                    re.compile("^(# )?var-base-path = .*"),
                    f'var-base-path = "{service.agent_var_base_path}"',
                ),
                (
                    re.compile("(# )?mount_path = .*"),
                    f'"{self.install_info.base_path / service.vfolder_relpath}"',
                ),
            ],
        )
        Path(self.install_info.service_config.agent_var_base_path).mkdir(
            parents=True, exist_ok=True
        )
        # TODO: enable CUDA plugin if nvidia stack is detected
        r"""
        if [ $ENABLE_CUDA -eq 1 ]; then
          sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = [\"ai.backend.accelerator.cuda_open\"]/" ./agent.toml
        elif [ $ENABLE_CUDA_MOCK -eq 1 ]; then
          sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = [\"ai.backend.accelerator.mock\"]/" ./agent.toml
        else
          sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = []/" ./agent.toml
        fi
        """

    async def configure_storage_proxy(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        toml_path = self.copy_config("storage-proxy.toml")
        self.sed_in_place_multi(
            toml_path,
            [
                ("port = 2379", f"port = {halfstack.etcd_addr[0].face.port}"),
                (
                    'secret = "some-secret-private-for-storage-proxy"',
                    f'secret = "{service.storage_proxy_auth_key}"',
                ),
                (
                    'secret = "some-secret-shared-with-manager"',
                    f'secret = "{service.manager_auth_key}"',
                ),
                (
                    re.compile("^(# )?ipc-base-path = .*"),
                    f'ipc-base-path = "{service.storage_proxy_ipc_base_path}"',
                ),
                (
                    re.compile("^(# )?var-base-path = .*"),  # unused yet
                    f'var-base-path = "{service.storage_proxy_var_base_path}"',
                ),
                # the halfstack toml already has [volume.volume1] section
                (
                    'path = "vfolder/local/volume1"',
                    f'path = "{service.vfolder_relpath}"',
                ),
            ],
        )

    async def configure_webserver(self) -> None:
        conf_path = self.copy_config("webserver.conf")
        service = self.install_info.service_config
        self.sed_in_place(
            conf_path,
            "https://api.backend.ai",
            f"http://{service.manager_addr.face.host}:{service.manager_addr.face.port}",
        )

    async def configure_webui(self) -> None:
        pass

    async def configure_client(self) -> None:
        r"""
        CLIENT_ADMIN_CONF_FOR_API="env-local-admin-api.sh"
        CLIENT_ADMIN_CONF_FOR_SESSION="env-local-admin-session.sh"
        echo "# Directly access to the manager using API keypair (admin)" > "${CLIENT_ADMIN_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_ADMIN_CONF_FOR_API}"
        echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="admin@lablup.com") | .access_key')" >> "${CLIENT_ADMIN_CONF_FOR_API}"
        echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="admin@lablup.com") | .secret_key')" >> "${CLIENT_ADMIN_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_ADMIN_CONF_FOR_API}"
        chmod +x "${CLIENT_ADMIN_CONF_FOR_API}"
        echo "# Indirectly access to the manager via the web server using a cookie-based login session (admin)" > "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"

        case $(basename $SHELL) in
          fish)
              echo "set -e BACKEND_ACCESS_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
              echo "set -e BACKEND_SECRET_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
          ;;
          *)
              echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
              echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
          ;;
        esac

        echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        echo "echo 'Username: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="admin") | .email')'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        echo "echo 'Password: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="admin") | .password')'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        chmod +x "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        CLIENT_DOMAINADMIN_CONF_FOR_API="env-local-domainadmin-api.sh"
        CLIENT_DOMAINADMIN_CONF_FOR_SESSION="env-local-domainadmin-session.sh"
        echo "# Directly access to the manager using API keypair (admin)" > "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
        echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="domain-admin@lablup.com") | .access_key')" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
        echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="domain-admin@lablup.com") | .secret_key')" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
        chmod +x "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
        echo "# Indirectly access to the manager via the web server using a cookie-based login session (admin)" > "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"

        case $(basename $SHELL) in
          fish)
              echo "set -e BACKEND_ACCESS_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
              echo "set -e BACKEND_SECRET_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
          ;;
          *)
              echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
              echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
          ;;
        esac

        echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        echo "echo 'Username: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="domain-admin") | .email')'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        echo "echo 'Password: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="domain-admin") | .password')'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        chmod +x "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        CLIENT_USER_CONF_FOR_API="env-local-user-api.sh"
        CLIENT_USER_CONF_FOR_SESSION="env-local-user-session.sh"
        echo "# Directly access to the manager using API keypair (user)" > "${CLIENT_USER_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_USER_CONF_FOR_API}"
        echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user@lablup.com") | .access_key')" >> "${CLIENT_USER_CONF_FOR_API}"
        echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user@lablup.com") | .secret_key')" >> "${CLIENT_USER_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_USER_CONF_FOR_API}"
        chmod +x "${CLIENT_USER_CONF_FOR_API}"
        CLIENT_USER2_CONF_FOR_API="env-local-user2-api.sh"
        CLIENT_USER2_CONF_FOR_SESSION="env-local-user2-session.sh"
        echo "# Directly access to the manager using API keypair (user2)" > "${CLIENT_USER2_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_USER2_CONF_FOR_API}"
        echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user2@lablup.com") | .access_key')" >> "${CLIENT_USER2_CONF_FOR_API}"
        echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user2@lablup.com") | .secret_key')" >> "${CLIENT_USER2_CONF_FOR_API}"
        echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_USER2_CONF_FOR_API}"
        chmod +x "${CLIENT_USER2_CONF_FOR_API}"
        echo "# Indirectly access to the manager via the web server using a cookie-based login session (user)" > "${CLIENT_USER_CONF_FOR_SESSION}"
        echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_USER_CONF_FOR_SESSION}"

        case $(basename $SHELL) in
          fish)
              echo "set -e BACKEND_ACCESS_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
              echo "set -e BACKEND_SECRET_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
          ;;
          *)
              echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
              echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
          ;;
        esac

        echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_USER_CONF_FOR_SESSION}"
        echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
        echo "echo 'Username: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="user") | .email')'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
        echo "echo 'Password: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="user") | .password')'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
        chmod +x "${CLIENT_USER_CONF_FOR_SESSION}"

        """

    async def dump_etcd_config(self) -> None:
        r"""
        ./backend.ai mgr etcd get --prefix '' > ./dev.etcd.installed.json
        """

    async def prepare_local_vfolder_host(self) -> None:
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        volume_root = Path(self.install_info.base_path / service.vfolder_relpath)
        volume_root.mkdir(parents=True, exist_ok=True)
        await asyncio.sleep(0)
        Path(volume_root / "version.txt").write_text("3")
        scratch_root = Path(self.install_info.base_path / "scratches")
        scratch_root.mkdir(parents=True, exist_ok=True)
        await asyncio.sleep(0)
        async with aclosing(
            await asyncpg.connect(
                host=halfstack.postgres_addr.face.host,
                port=halfstack.postgres_addr.face.port,
                user=halfstack.postgres_user,
                password=halfstack.postgres_password,
                database="backend",
            )
        ) as conn:
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
            await conn.execute(
                "UPDATE domains SET allowed_vfolder_hosts = $1",
                {"local:volume1": default_vfolder_host_perms},
            )
            await conn.execute(
                "UPDATE groups SET allowed_vfolder_hosts = $1",
                {"local:volume1": default_vfolder_host_perms},
            )
            await conn.execute(
                "UPDATE keypair_resource_policies SET allowed_vfolder_hosts = $1",
                {"local:volume1": default_vfolder_host_perms},
            )
            await conn.execute(
                "UPDATE vfolders SET host = $1",
                "local:volume1",
            )

    async def populate_images(self) -> None:
        if self.os_info.platform in (Platform.LINUX_ARM64, Platform.MACOS_ARM64):
            project = "stable,community,multiarch"
        else:
            project = "stable,community"
        data: Any = {
            "docker": {
                "registry": {
                    "cr.backend.ai": {
                        "": "https://cr.backend.ai",
                        "type": "harbor2",
                        "project": project,
                    },
                },
            },
        }
        await self.put_etcd_json("config", data)
        if self.os_info.platform in (Platform.LINUX_ARM64, Platform.MACOS_ARM64):
            await self.run_manager_cli(
                [
                    "mgr",
                    "image",
                    "alias",
                    "python",
                    "cr.backend.ai/stable/python:3.9-ubuntu20.04",
                    "aarch64",
                ]
            )
        else:
            await self.run_manager_cli(
                [
                    "mgr",
                    "image",
                    "alias",
                    "python",
                    "cr.backend.ai/stable/python:3.9-ubuntu20.04",
                    "x86_64",
                ]
            )


class DevContext(Context):
    def hydrate_install_info(self) -> InstallInfo:
        # TODO: customize addr/user/password options
        # TODO: multi-node setup
        halfstack_config = HalfstackConfig(
            ha_setup=False,
            postgres_addr=ServerAddr(HostPortPair("127.0.0.1", 8101)),
            postgres_user="postgres",
            postgres_password="develove",
            redis_addr=ServerAddr(HostPortPair("127.0.0.1", 8111)),
            redis_sentinel_addrs=[],
            redis_password="develove",
            etcd_addr=[ServerAddr(HostPortPair("127.0.0.1", 8121))],
            etcd_user=None,
            etcd_password=None,
        )
        service_config = ServiceConfig(
            webserver_addr=ServerAddr(HostPortPair("127.0.0.1", 8090)),
            webserver_ipc_base_path="ipc/webserver",
            webserver_var_base_path="var/webserver",
            manager_addr=ServerAddr(HostPortPair("127.0.0.1", 8091)),
            manager_auth_key=secrets.token_hex(32),
            manager_ipc_base_path="ipc/manager",
            manager_var_base_path="var/manager",
            agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6011)),
            agent_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6019)),
            agent_ipc_base_path="ipc/agent",
            agent_var_base_path="var/agent",
            storage_proxy_manager_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6021)),
            storage_proxy_client_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6022)),
            storage_proxy_ipc_base_path="ipc/storage-proxy",
            storage_proxy_var_base_path="var/storage-proxy",
            storage_proxy_auth_key=secrets.token_hex(32),
            storage_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6029)),
            storage_agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6012)),
            storage_agent_ipc_base_path="ipc/storage-agent",
            storage_agent_var_base_path="var/storage-agent",
            vfolder_relpath="vfolder/local/volume1",
        )
        return InstallInfo(
            version=self.dist_info.version,
            base_path=self.dist_info.target_path,
            type=InstallType.SOURCE,
            last_updated=datetime.now(tzutc()),
            halfstack_config=halfstack_config,
            service_config=service_config,
        )

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
        await self.install_halfstack()

    async def _configure_mock_accelerator(self) -> None:
        """
        cp "configs/accelerator/mock-accelerator.toml" mock-accelerator.toml
        """

    async def configure(self) -> None:
        self.log_header("Configuring manager...")
        await self.configure_manager()
        self.log_header("Configuring agent...")
        await self.configure_agent()
        self.log_header("Configuring storage-proxy...")
        await self.configure_storage_proxy()
        self.log_header("Configuring webserver and webui...")
        await self.configure_webserver()
        await self.configure_webui()
        self.log_header("Loading fixtures...")
        await self.load_fixtures()
        self.log_header("Preparing vfolder volumes...")
        await self.prepare_local_vfolder_host()

    async def populate_images(self) -> None:
        # TODO: docker pull
        pass


class PackageContext(Context):
    def hydrate_install_info(self) -> InstallInfo:
        # TODO: customize addr/user/password options
        # TODO: multi-node setup
        halfstack_config = HalfstackConfig(
            ha_setup=False,
            postgres_addr=ServerAddr(HostPortPair("127.0.0.1", 8101)),
            postgres_user="postgres",
            postgres_password="develove",
            redis_addr=ServerAddr(HostPortPair("127.0.0.1", 8111)),
            redis_sentinel_addrs=[],
            redis_password="develove",
            etcd_addr=[ServerAddr(HostPortPair("127.0.0.1", 8121))],
            etcd_user=None,
            etcd_password=None,
        )
        service_config = ServiceConfig(
            webserver_addr=ServerAddr(HostPortPair("127.0.0.1", 8090)),
            webserver_ipc_base_path="ipc/webserver",
            webserver_var_base_path="var/webserver",
            manager_addr=ServerAddr(HostPortPair("127.0.0.1", 8091)),
            manager_auth_key=secrets.token_urlsafe(32),
            manager_ipc_base_path="ipc/manager",
            manager_var_base_path="var/manager",
            agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6011)),
            agent_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6019)),
            agent_ipc_base_path="ipc/agent",
            agent_var_base_path="var/agent",
            storage_proxy_manager_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6021)),
            storage_proxy_client_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6022)),
            storage_proxy_ipc_base_path="ipc/storage-proxy",
            storage_proxy_var_base_path="var/storage-proxy",
            storage_proxy_auth_key=secrets.token_urlsafe(32),
            storage_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6029)),
            storage_agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6012)),
            storage_agent_ipc_base_path="ipc/storage-agent",
            storage_agent_var_base_path="var/storage-agent",
            vfolder_relpath="vfolder/local/volume1",
        )
        return InstallInfo(
            version=self.dist_info.version,
            base_path=self.dist_info.target_path,
            type=InstallType.PACKAGE,
            last_updated=datetime.now(tzutc()),
            halfstack_config=halfstack_config,
            service_config=service_config,
        )

    async def check_prerequisites(self) -> None:
        self.os_info = await detect_os(self)
        await check_docker(self)
        if self.os_info.distro == "Darwin":
            await check_docker_desktop_mount(self)

    def _mangle_pkgname(self, name: str, fat: bool = False) -> str:
        # local-proxy does not have fat variant. (It is always fat.)
        if fat and name != "backendai-local-proxy":
            return f"backendai-{name}-fat-{self.os_info.platform}"
        return f"backendai-{name}-{self.os_info.platform}"

    async def _validate_checksum(self, pkg_path: Path, csum_path: Path) -> None:
        proc = await asyncio.create_subprocess_exec(
            *["sha256sum", "-c", csum_path.name],
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
        pkg_name = self._mangle_pkgname(name)
        dst_path = self.dist_info.target_path / pkg_name
        csum_path = dst_path.with_name(pkg_name + ".sha256")
        pkg_url = f"https://github.com/lablup/backend.ai/releases/download/{self.dist_info.version}/{pkg_name}"
        csum_url = pkg_url + ".sha256"
        self.log.write(f"Downloading {pkg_url}...")
        item = Static(classes="progress-item")
        label = Label(Text.from_markup(f"[blue](download)[/] {pkg_name}"), classes="progress-name")
        progress = ProgressBar(classes="progress-download")
        item.mount_all([label, progress])
        vpane.mount(item)
        async with self.wget_sema:
            await wget(pkg_url, dst_path, progress)
            await wget(csum_url, csum_path)

    async def _verify_package(self, name: str, *, fat: bool) -> None:
        pkg_name = self._mangle_pkgname(name, fat=fat)
        dst_path = self.dist_info.target_path / pkg_name
        self.log.write(f"Verifying {dst_path} ...")
        csum_path = dst_path.with_name(pkg_name + ".sha256")
        await self._validate_checksum(dst_path, csum_path)
        csum_path.unlink()
        dst_path.rename(dst_path.with_name(f"backendai-{name}"))

    async def _install_package(self, name: str, vpane: Vertical, *, fat: bool) -> None:
        pkg_name = self._mangle_pkgname(name, fat=fat)
        src_path = self.dist_info.package_dir / pkg_name
        dst_path = self.dist_info.target_path / pkg_name
        item = Static(classes="progress-item")
        label = Label(Text.from_markup(f"[blue](install)[/] {pkg_name}"), classes="progress-name")
        progress = ProgressBar(classes="progress-install")
        item.mount_all([label, progress])
        vpane.mount(item)
        async with (
            aiofiles.open(src_path, "rb") as src,
            aiofiles.open(dst_path, "wb") as dst,
        ):
            progress.update(total=src_path.stat().st_size)
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
                        tg.create_task(self._fetch_package("local-proxy", vpane))
                        tg.create_task(self._fetch_package("storage-proxy", vpane))
                        tg.create_task(self._fetch_package("client", vpane))
                    # Verify the checksums of the downloaded packages.
                    await self._verify_package("manager", fat=False)
                    await self._verify_package("agent", fat=False)
                    await self._verify_package("agent-watcher", fat=False)
                    await self._verify_package("webserver", fat=False)
                    await self._verify_package("local-proxy", fat=False)
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
                        "local-proxy", vpane, fat=self.dist_info.use_fat_binary
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
                    await self._verify_package("local-proxy", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("storage-proxy", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("client", fat=self.dist_info.use_fat_binary)
        finally:
            vpane.remove()
        self.log_header("Installing databases (halfstack)...")
        await self.install_halfstack()

    async def configure(self) -> None:
        self.log_header("Configuring manager...")
        await self.configure_manager()
        self.log_header("Configuring agent...")
        await self.configure_agent()
        self.log_header("Configuring storage-proxy...")
        await self.configure_storage_proxy()
        self.log_header("Configuring webserver and webui...")
        await self.configure_webserver()
        await self.configure_webui()
        self.log_header("Loading fixtures...")
        await self.load_fixtures()
        self.log_header("Preparing vfolder volumes...")
        await self.prepare_local_vfolder_host()
        # TODO: install as systemd services?

    async def populate_images(self) -> None:
        # TODO: docker load
        self.log_header("Loading docker images...")
        pass
