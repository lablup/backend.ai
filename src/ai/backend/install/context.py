from __future__ import annotations

import asyncio
import enum
import importlib.resources
import json
import os
import random
import re
import secrets
import shutil
import tempfile
from abc import ABCMeta, abstractmethod
from contextlib import asynccontextmanager as actxmgr
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, AsyncIterator, Final, Iterator, Sequence

import aiofiles
import aiotools
import asyncpg
import tomlkit
from dateutil.tz import tzutc
from rich.text import Text
from textual.app import App
from textual.containers import Vertical
from textual.widgets import Label, ProgressBar, Static

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes

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
    DistInfo,
    HalfstackConfig,
    HostPortPair,
    ImageSource,
    InstallInfo,
    InstallType,
    InstallVariable,
    OSInfo,
    PackageSource,
    Platform,
    ServerAddr,
    ServiceConfig,
)
from .widgets import SetupLog

current_log: ContextVar[SetupLog] = ContextVar("current_log")
PASSPHRASE_CHARACTER_POOL: Final[list[str]] = (
    [chr(x) for x in range(ord("a"), ord("z") + 1)]
    + [chr(x) for x in range(ord("A"), ord("Z") + 1)]
    + [chr(x) for x in range(ord("0"), ord("9") + 1)]
    + ["*$./"]
)


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
        app: App,
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

    def add_post_guide(self, guide: PostGuide) -> None:
        self._post_guides.append(guide)

    def show_post_guide(self) -> None:
        pass

    def log_header(self, title: str) -> None:
        self.log.write(Text.from_markup(f"[bright_green]:green_circle: {title}"))

    def mangle_pkgname(self, name: str, fat: bool = False) -> str:
        return f"backendai-{name}-{self.os_info.platform}"

    def generate_passphrase(self, len=16) -> str:
        return "".join(random.sample(PASSPHRASE_CHARACTER_POOL, len))

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
        with self.resource_path("ai.backend.install.configs", template_name) as src_path:
            dst_path = self.dist_info.target_path / template_name
            dst_path.parent.mkdir(parents=True, exist_ok=True)
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

    @actxmgr
    async def etcd_ctx(self) -> AsyncIterator[AsyncEtcd]:
        halfstack = self.install_info.halfstack_config
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
        }
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
            yield etcd
        finally:
            await etcd.close()

    async def etcd_put_json(self, key: str, value: Any) -> None:
        async with self.etcd_ctx() as etcd:
            await etcd.put_prefix(key, value, scope=ConfigScopes.GLOBAL)

    async def etcd_get_json(self, key: str) -> Any:
        async with self.etcd_ctx() as etcd:
            return await etcd.get_prefix(key, scope=ConfigScopes.GLOBAL)

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
                ("8110:6379", f"{self.install_info.halfstack_config.redis_addr.bind.port}:6379"),
                ("8120:2379", f"{self.install_info.halfstack_config.etcd_addr[0].bind.port}:2379"),
            ],
        )
        sudo = " ".join(self.docker_sudo)
        await self.run_shell(
            f"""
        {sudo} docker compose pull && \\
        {sudo} docker compose up -d --wait backendai-half-db && \\
        {sudo} docker compose up -d && \\
        {sudo} docker compose ps
        """,
            cwd=self.install_info.base_path,
        )

    async def load_fixtures(self) -> None:
        await self.run_manager_cli(["mgr", "schema", "oneshot"])
        with self.resource_path("ai.backend.install.fixtures", "example-users.json") as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path("ai.backend.install.fixtures", "example-keypairs.json") as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-set-user-main-access-keys.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with self.resource_path(
            "ai.backend.install.fixtures", "example-resource-presets.json"
        ) as path:
            await self.run_manager_cli(["mgr", "fixture", "populate", str(path)])
        with tempfile.TemporaryDirectory() as tmpdir:
            service = self.install_info.service_config
            fixture_path = Path(tmpdir) / "fixture.json"
            with open(fixture_path, "w") as fw:
                fw.write(
                    json.dumps({
                        "__mode": "update",
                        "scaling_groups": [
                            {
                                "name": "default",
                                "wsproxy_addr": f"http://{service.local_proxy_addr.face.host}:{service.local_proxy_addr.face.port}",
                                "wsproxy_api_token": service.wsproxy_api_token,
                            }
                        ],
                    })
                )
            await self.run_manager_cli(["mgr", "fixture", "populate", fixture_path.as_posix()])

    async def check_prerequisites(self) -> None:
        self.os_info = await detect_os()
        text = Text()
        text.append("Detetced OS info: ")
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
                        "manager_api": f"http://{storage_manager_facing_addr.face.host}:{storage_manager_facing_addr.face.port}",
                        "secret": self.install_info.service_config.storage_proxy_manager_auth_key,
                        "ssl_verify": "false",
                    }
                },
                "exposed_volume_info": "percentage",
            },
        }
        await self.etcd_put_json("", data)
        data = {}
        # TODO: in dev-mode, enable these.
        data["api"] = {}
        data["api"]["allow-openapi-schema-introspection"] = "no"
        data["api"]["allow-graphql-schema-introspection"] = "no"
        if halfstack.ha_setup:
            assert halfstack.redis_sentinel_addrs
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
            assert halfstack.redis_addr
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
        # enable the CUDA plugin (open-source version)
        # The agent will show an error log if the CUDA is not available in the system and report
        # "cuda.devices = 0" as the agent capacity, but it will still run.
        self.sed_in_place(
            toml_path,
            re.compile("^(# )?allow-compute-plugins = .*"),
            'allow-compute-plugins = ["ai.backend.accelerator.cuda_open"]',
        )
        # TODO: let the installer enable the CUDA plugin only when it verifies CUDA availability or
        #       via an explicit installer option/config.
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
            data["volume"]["volume1"]["path"] = service.vfolder_relpath  # type: ignore
        with toml_path.open("w") as fp:
            tomlkit.dump(data, fp)

    async def configure_webserver(self) -> None:
        conf_path = self.copy_config("webserver.conf")
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        assert halfstack.redis_addr is not None
        with conf_path.open("r") as fp:
            data = tomlkit.load(fp)
            wsproxy_itable = tomlkit.inline_table()
            wsproxy_itable["url"] = (
                f"http://{service.local_proxy_addr.face.host}:{service.local_proxy_addr.face.port}"
            )
            data["service"]["wsproxy"] = wsproxy_itable  # type: ignore
            data["api"][  # type: ignore
                "endpoint"
            ] = f"http://{service.manager_addr.face.host}:{service.manager_addr.face.port}"
            helper_table = tomlkit.table()
            helper_table["socket_timeout"] = 5.0
            helper_table["socket_connect_timeout"] = 2.0
            helper_table["reconnect_poll_timeout"] = 0.3
            if halfstack.ha_setup:
                assert halfstack.redis_sentinel_addrs
                redis_table = tomlkit.table()
                redis_table["sentinel"] = ",".join(
                    f"{binding.host}:{binding.port}" for binding in halfstack.redis_sentinel_addrs
                )
                redis_table["service_name"] = "mymaster"
                redis_table["redis_helper_config"] = helper_table
                if halfstack.redis_password:
                    redis_table["password"] = halfstack.redis_password
            else:
                assert halfstack.redis_addr
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

    async def configure_wsproxy(self) -> None:
        conf_path = self.copy_config("wsproxy.toml")
        halfstack = self.install_info.halfstack_config
        service = self.install_info.service_config
        assert halfstack.redis_addr is not None
        with conf_path.open("r") as fp:
            data = tomlkit.load(fp)
            data["wsproxy"]["bind_host"] = service.local_proxy_addr.bind.host  # type: ignore
            data["wsproxy"]["advertised_host"] = service.local_proxy_addr.face.host  # type: ignore
            data["wsproxy"]["bind_api_port"] = service.local_proxy_addr.bind.port  # type: ignore
            data["wsproxy"]["advertised_api_port"] = service.local_proxy_addr.face.port  # type: ignore
            data["wsproxy"]["jwt_encrypt_key"] = service.wsproxy_jwt_key  # type: ignore
            data["wsproxy"]["permit_hash_key"] = service.wsproxy_hash_key  # type: ignore
            data["wsproxy"]["api_secret"] = service.wsproxy_api_token  # type: ignore
        with conf_path.open("w") as fp:
            tomlkit.dump(data, fp)

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

    async def configure_client(self) -> None:
        # TODO: add an option to generate keypairs
        base_path = self.install_info.base_path
        service = self.install_info.service_config
        with self.resource_path(
            "ai.backend.install.fixtures", "example-keypairs.json"
        ) as keypair_path:
            current_shell = os.environ.get("SHELL", "sh")
            keypair_data = json.loads(Path(keypair_path).read_bytes())
        for keypair in keypair_data["keypairs"]:
            email = keypair["user_id"]
            if match := re.search(r"^(\w+)@", email):
                username = match.group(1)
            else:
                continue
            with open(base_path / f"env-local-{username}-api.sh", "w") as fp:
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
            with open(base_path / f"env-local-{username}-session.sh", "w") as fp:
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
                print(f"""echo 'Your email: {user['email']}'""", file=fp)
                print(f"""echo 'Your password: {user['password']}'""", file=fp)

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
        async with aiotools.closing_async(
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
                    if self.os_info.platform in (Platform.LINUX_ARM64, Platform.MACOS_ARM64):
                        project = "stable,community,multiarch"
                    else:
                        project = "stable,community"
                    data = {
                        "docker": {
                            "image": {
                                "auto_pull": "tag",  # FIXME: temporary workaround for multiarch
                            },
                            "registry": {
                                "cr.backend.ai": {
                                    "": "https://cr.backend.ai",
                                    "type": "harbor2",
                                    "project": project,
                                },
                            },
                        },
                    }
                    await self.etcd_put_json("config", data)
                    await self.run_manager_cli(["mgr", "image", "rescan", "cr.backend.ai"])
                    if self.os_info.platform in (Platform.LINUX_ARM64, Platform.MACOS_ARM64):
                        await self.alias_image(
                            "python",
                            "cr.backend.ai/stable/python:3.9-ubuntu20.04",
                            "aarch64",
                        )
                    else:
                        await self.alias_image(
                            "python",
                            "cr.backend.ai/stable/python:3.9-ubuntu20.04",
                            "x86_64",
                        )
                case ImageSource.DOCKER_HUB:
                    self.log_header(
                        "Scanning and pulling configured Docker Hub container images..."
                    )
                    data = {
                        "docker": {
                            "image": {
                                "auto_pull": "tag",  # FIXME: temporary workaround for multiarch
                            },
                            "registry": {
                                "index.docker.io": {
                                    "": "https://registry-1.docker.io",
                                    "type": "docker",
                                    "username": "lablup",
                                },
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
                    raise NotImplementedError()


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
            agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6011)),
            agent_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6019)),
            agent_ipc_base_path="ipc/agent",
            agent_var_base_path="var/agent",
            storage_proxy_manager_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6021)),
            storage_proxy_client_facing_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 6022),
                face=HostPortPair(public_facing_address, 6022),
            ),
            storage_proxy_ipc_base_path="ipc/storage-proxy",
            storage_proxy_var_base_path="var/storage-proxy",
            storage_proxy_random=secrets.token_hex(32),
            storage_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6029)),
            storage_agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6012)),
            storage_agent_ipc_base_path="ipc/storage-agent",
            storage_agent_var_base_path="var/storage-agent",
            vfolder_relpath="vfolder/local/volume1",
            wsproxy_hash_key=self.generate_passphrase(),
            wsproxy_jwt_key=self.generate_passphrase(),
            wsproxy_api_token=self.generate_passphrase(),
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
        self.log_header("Configuring wsproxy...")
        await self.configure_wsproxy()
        self.log_header("Generating client environ configs...")
        await self.configure_client()
        self.log_header("Loading fixtures...")
        await self.load_fixtures()
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
            agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6011)),
            agent_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6019)),
            agent_ipc_base_path="ipc/agent",
            agent_var_base_path="var/agent",
            storage_proxy_manager_facing_addr=ServerAddr(HostPortPair("127.0.0.1", 6021)),
            storage_proxy_client_facing_addr=ServerAddr(
                bind=HostPortPair(public_component_bind_address, 6022),
                face=HostPortPair(public_facing_address, 6022),
            ),
            storage_proxy_ipc_base_path="ipc/storage-proxy",
            storage_proxy_var_base_path="var/storage-proxy",
            storage_proxy_random=secrets.token_urlsafe(32),
            storage_watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6029)),
            storage_agent_rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6012)),
            storage_agent_ipc_base_path="ipc/storage-agent",
            storage_agent_var_base_path="var/storage-agent",
            vfolder_relpath="vfolder/local/volume1",
            wsproxy_hash_key=self.generate_passphrase(),
            wsproxy_jwt_key=self.generate_passphrase(),
            wsproxy_api_token=self.generate_passphrase(),
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
        await super().check_prerequisites()

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
        pkg_name = self.mangle_pkgname(name, fat=fat)
        dst_path = self.dist_info.target_path / pkg_name
        self.log.write(f"Verifying {dst_path} ...")
        csum_path = dst_path.with_name(pkg_name + ".sha256")
        await self._validate_checksum(dst_path, csum_path)
        csum_path.unlink()
        dst_path.chmod(0o755)
        dst_path.rename(dst_path.with_name(f"backendai-{name}"))

    async def _install_package(self, name: str, vpane: Vertical, *, fat: bool) -> None:
        self.dist_info.target_path.mkdir(parents=True, exist_ok=True)
        pkg_name = self.mangle_pkgname(name, fat=fat)
        src_path = self.dist_info.package_dir / pkg_name
        dst_path = self.dist_info.target_path / pkg_name
        item = Static(classes="progress-item")
        label = Label(Text.from_markup(f"[blue](install)[/] {pkg_name}"), classes="progress-name")
        progress = ProgressBar(classes="progress-install")
        item.mount_all([label, progress])
        vpane.mount(item)
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
                        tg.create_task(self._fetch_package("wsproxy", vpane))
                        tg.create_task(self._fetch_package("storage-proxy", vpane))
                        tg.create_task(self._fetch_package("client", vpane))
                    # Verify the checksums of the downloaded packages.
                    await self._verify_package("manager", fat=False)
                    await self._verify_package("agent", fat=False)
                    await self._verify_package("agent-watcher", fat=False)
                    await self._verify_package("webserver", fat=False)
                    await self._verify_package("wsproxy", fat=False)
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
                    await self._install_package("wsproxy", vpane, fat=self.dist_info.use_fat_binary)
                    await self._install_package(
                        "storage-proxy", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package("client", vpane, fat=self.dist_info.use_fat_binary)
                    # Verify the checksums.
                    await self._verify_package("manager", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("agent", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("agent-watcher", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("webserver", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("wsproxy", fat=self.dist_info.use_fat_binary)
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
        self.log_header("Configuring wsproxy...")
        await self.configure_wsproxy()
        self.log_header("Generating client environ configs...")
        await self.configure_client()
        self.log_header("Loading fixtures...")
        await self.load_fixtures()
        self.log_header("Preparing vfolder volumes...")
        await self.prepare_local_vfolder_host()
        # TODO: install as systemd services?
