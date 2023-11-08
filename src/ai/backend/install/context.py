from __future__ import annotations

import asyncio
import enum
from contextvars import ContextVar
from pathlib import Path

import aiofiles
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

    async def install_halfstack(self, *, ha_setup: bool) -> None:
        r"""
        SOURCE_COMPOSE_PATH="docker-compose.halfstack-${CURRENT_BRANCH//.}.yml"
        if [ ! -f "${SOURCE_COMPOSE_PATH}" ]; then
          SOURCE_COMPOSE_PATH="docker-compose.halfstack-main.yml"
        fi
        cp "${SOURCE_COMPOSE_PATH}" "docker-compose.halfstack.current.yml"

        sed_inplace "s/8100:5432/${POSTGRES_PORT}:5432/" "docker-compose.halfstack.current.yml"
        sed_inplace "s/8110:6379/${REDIS_PORT}:6379/" "docker-compose.halfstack.current.yml"
        sed_inplace "s/8120:2379/${ETCD_PORT}:2379/" "docker-compose.halfstack.current.yml"

        mkdir -p "${HALFSTACK_VOLUME_PATH}/postgres-data"
        mkdir -p "${HALFSTACK_VOLUME_PATH}/etcd-data"
        mkdir -p "${HALFSTACK_VOLUME_PATH}/redis-data"

        $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" pull
        $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" up -d
        $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" ps   # You should see three containers here.
        """

    async def load_fixtures(self) -> None:
        r"""
        ./backend.ai mgr schema oneshot
        ./backend.ai mgr fixture populate fixtures/manager/example-keypairs.json
        ./backend.ai mgr fixture populate fixtures/manager/example-resource-presets.json

        ./backend.ai mgr etcd put config/docker/registry/cr.backend.ai "https://cr.backend.ai"
        ./backend.ai mgr etcd put config/docker/registry/cr.backend.ai/type "harbor2"
        if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
          ./backend.ai mgr etcd put config/docker/registry/cr.backend.ai/project "stable,community,multiarch"
        else
          ./backend.ai mgr etcd put config/docker/registry/cr.backend.ai/project "stable,community"
        fi

        ./backend.ai mgr image rescan cr.backend.ai
        if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
          ./backend.ai mgr image alias python "cr.backend.ai/multiarch/python:3.9-ubuntu20.04" aarch64
        else
          ./backend.ai mgr image alias python "cr.backend.ai/stable/python:3.9-ubuntu20.04" x86_64
        fi
        """

    async def configure_manager(self) -> None:
        r"""
        cp configs/manager/halfstack.toml ./manager.toml
        sed_inplace "s/num-proc = .*/num-proc = 1/" ./manager.toml
        sed_inplace "s/port = 8120/port = ${ETCD_PORT}/" ./manager.toml
        sed_inplace "s/port = 8100/port = ${POSTGRES_PORT}/" ./manager.toml
        sed_inplace "s/port = 8081/port = ${MANAGER_PORT}/" ./manager.toml
        sed_inplace "s@\(# \)\{0,1\}ipc-base-path = .*@ipc-base-path = "'"'"${IPC_BASE_PATH}"'"'"@" ./manager.toml
        cp configs/manager/halfstack.alembic.ini ./alembic.ini
        sed_inplace "s/localhost:8100/localhost:${POSTGRES_PORT}/" ./alembic.ini

        if [ $CONFIGURE_HA -eq 1 ]; then
          ./backend.ai mgr etcd put config/redis/sentinel "127.0.0.1:${REDIS_SENTINEL1_PORT},127.0.0.1:${REDIS_SENTINEL2_PORT},127.0.0.1:${REDIS_SENTINEL3_PORT}"
          ./backend.ai mgr etcd put config/redis/service_name "mymaster"
          ./backend.ai mgr etcd put config/redis/password "develove"
        else
          ./backend.ai mgr etcd put config/redis/addr "127.0.0.1:${REDIS_PORT}"
        fi

        ./backend.ai mgr etcd put-json config/redis/redis_helper_config ./configs/manager/sample.etcd.redis-helper.json

        cp configs/manager/sample.etcd.volumes.json ./dev.etcd.volumes.json
        MANAGER_AUTH_KEY=$(python -c 'import secrets; print(secrets.token_hex(32), end="")')
        sed_inplace "s/\"secret\": \"some-secret-shared-with-storage-proxy\"/\"secret\": \"${MANAGER_AUTH_KEY}\"/" ./dev.etcd.volumes.json
        sed_inplace "s/\"default_host\": .*$/\"default_host\": \"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\",/" ./dev.etcd.volumes.json
        """

    async def configure_agent(self) -> None:
        r"""
        cp configs/agent/halfstack.toml ./agent.toml
        mkdir -p "$VAR_BASE_PATH"
        sed_inplace "s/port = 8120/port = ${ETCD_PORT}/" ./agent.toml
        sed_inplace "s/port = 6001/port = ${AGENT_RPC_PORT}/" ./agent.toml
        sed_inplace "s/port = 6009/port = ${AGENT_WATCHER_PORT}/" ./agent.toml
        sed_inplace "s@\(# \)\{0,1\}ipc-base-path = .*@ipc-base-path = "'"'"${IPC_BASE_PATH}"'"'"@" ./agent.toml
        sed_inplace "s@\(# \)\{0,1\}var-base-path = .*@var-base-path = "'"'"${VAR_BASE_PATH}"'"'"@" ./agent.toml

        # configure backend mode
        if [ $AGENT_BACKEND = "k8s" ] || [ $AGENT_BACKEND = "kubernetes" ]; then
          sed_inplace "s/mode = \"docker\"/mode = \"kubernetes\"/" ./agent.toml
          sed_inplace "s/scratch-type = \"hostdir\"/scratch-type = \"k8s-nfs\"/" ./agent.toml
        elif [ $AGENT_BACKEND = "docker" ]; then
          sed '/scratch-nfs-/d' ./agent.toml > ./agent.toml.sed
          mv ./agent.toml.sed ./agent.toml
        fi
        sed_inplace "s@\(# \)\{0,1\}mount-path = .*@mount-path = "'"'"${ROOT_PATH}/${VFOLDER_REL_PATH}"'"'"@" ./agent.toml
        if [ $ENABLE_CUDA -eq 1 ]; then
          sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = [\"ai.backend.accelerator.cuda_open\"]/" ./agent.toml
        elif [ $ENABLE_CUDA_MOCK -eq 1 ]; then
          sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = [\"ai.backend.accelerator.mock\"]/" ./agent.toml
        else
          sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = []/" ./agent.toml
        fi
        """

    async def configure_storage_proxy(self) -> None:
        r"""
        cp configs/storage-proxy/sample.toml ./storage-proxy.toml
        STORAGE_PROXY_RANDOM_KEY=$(python -c 'import secrets; print(secrets.token_hex(32), end="")')
        sed_inplace "s/port = 2379/port = ${ETCD_PORT}/" ./storage-proxy.toml
        sed_inplace "s/secret = \"some-secret-private-for-storage-proxy\"/secret = \"${STORAGE_PROXY_RANDOM_KEY}\"/" ./storage-proxy.toml
        sed_inplace "s/secret = \"some-secret-shared-with-manager\"/secret = \"${MANAGER_AUTH_KEY}\"/" ./storage-proxy.toml
        sed_inplace "s@\(# \)\{0,1\}ipc-base-path = .*@ipc-base-path = "'"'"${IPC_BASE_PATH}"'"'"@" ./storage-proxy.toml
        # comment out all sample volumes
        sed_inplace "s/^\[volume\./# \[volume\./" ./storage-proxy.toml
        sed_inplace "s/^backend =/# backend =/" ./storage-proxy.toml
        sed_inplace "s/^path =/# path =/" ./storage-proxy.toml
        sed_inplace "s/^purity/# purity/" ./storage-proxy.toml
        sed_inplace "s/^netapp_/# netapp_/" ./storage-proxy.toml
        sed_inplace "s/^weka_/# weka_/" ./storage-proxy.toml
        sed_inplace "s/^gpfs_/# gpfs_/" ./storage-proxy.toml
        sed_inplace "s/^vast_/# vast_/" ./storage-proxy.toml
        # add LOCAL_STORAGE_VOLUME vfs volume
        echo "\n[volume.${LOCAL_STORAGE_VOLUME}]\nbackend = \"vfs\"\npath = \"${ROOT_PATH}/${VFOLDER_REL_PATH}\"" >> ./storage-proxy.toml
        """

    async def configure_webserver(self) -> None:
        r"""
        cp configs/webserver/halfstack.conf ./webserver.conf
        sed_inplace "s/https:\/\/api.backend.ai/http:\/\/127.0.0.1:${MANAGER_PORT}/" ./webserver.conf
        """

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
        r"""
        VFOLDER_VERSION="3"
        VFOLDER_VERSION_TXT="version.txt"
        show_info "Setting up virtual folder..."
        mkdir -p "${ROOT_PATH}/${VFOLDER_REL_PATH}"
        echo "${VFOLDER_VERSION}" > "${ROOT_PATH}/${VFOLDER_REL_PATH}/${VFOLDER_VERSION_TXT}"
        ./backend.ai mgr etcd put-json volumes "./dev.etcd.volumes.json"
        mkdir -p scratches
        POSTGRES_CONTAINER_ID=$($docker_sudo docker compose -f "docker-compose.halfstack.current.yml" ps | grep "[-_]backendai-half-db[-_]1" | awk '{print $1}')
        ALL_VFOLDER_HOST_PERM='["create-vfolder","modify-vfolder","delete-vfolder","mount-in-session","upload-file","download-file","invite-others","set-user-specific-permission"]'
        $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update domains set allowed_vfolder_hosts = '{\"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\": ${ALL_VFOLDER_HOST_PERM}}';"
        $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update groups set allowed_vfolder_hosts = '{\"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\": ${ALL_VFOLDER_HOST_PERM}}';"
        $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update keypair_resource_policies set allowed_vfolder_hosts = '{\"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\": ${ALL_VFOLDER_HOST_PERM}}';"
        $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update vfolders set host = '${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}' where host='${LOCAL_STORAGE_VOLUME}';"

        """

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
        await self.install_halfstack(ha_setup=False)

    async def _configure_mock_accelerator(self) -> None:
        """
        cp "configs/accelerator/mock-accelerator.toml" mock-accelerator.toml
        """

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

    async def _validate_checksum(self, pkg_path: Path, csum_path: Path) -> None:
        proc = await asyncio.create_subprocess_exec(
            *["sha256sum", "-c", str(csum_path)],
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
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
        pkg_path = self.dist_info.target_path / pkg_name
        csum_path = pkg_path.with_name(pkg_name + ".sha256")
        pkg_url = f"https://github.com/lablup/backend.ai/releases/download/{self.dist_info.version}/{pkg_name}"
        csum_url = pkg_url + ".sha256"
        self.log.write(f"Downloading {pkg_url}...")
        item = Static(classes="progress-item")
        label = Label(Text.from_markup(f"[blue](download)[/] {pkg_name}"), classes="progress-name")
        progress = ProgressBar(classes="progress-download")
        item.mount_all([label, progress])
        await vpane.mount(item)
        async with self.wget_sema:
            try:
                await wget(pkg_url, pkg_path, progress)
                await wget(csum_url, csum_path)
            finally:
                item.remove()

    async def _verify_package(self, name: str, *, fat: bool) -> None:
        pkg_name = self._mangle_pkgname(name, fat=fat)
        pkg_path = self.dist_info.package_dir / pkg_name
        self.log.write(f"Verifying {pkg_path} ...")
        csum_path = pkg_path.with_name(pkg_name + ".sha256")
        await self._validate_checksum(pkg_path, csum_path)

    async def _install_package(self, name: str, vpane: Vertical, *, fat: bool) -> None:
        pkg_name = self._mangle_pkgname(name, fat=fat)
        src_path = self.dist_info.package_dir / pkg_name
        dst_path = self.dist_info.target_path / pkg_name
        item = Static(classes="progress-item")
        label = Label(Text.from_markup(f"[blue](install)[/] {pkg_name}"), classes="progress-name")
        progress = ProgressBar(classes="progress-install")
        item.mount_all([label, progress])
        await vpane.mount(item)
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
                        # TODO: tg.create_task(self._fetch_package("wsproxy", vpane))
                        tg.create_task(self._fetch_package("storage-proxy", vpane))
                        tg.create_task(self._fetch_package("client", vpane))
                    # Verify the checksums of the downloaded packages.
                    ## await self._verify_package("manager", fat=False)
                    ## await self._verify_package("agent", fat=False)
                    ## await self._verify_package("agent-watcher", fat=False)
                    ## await self._verify_package("webserver", fat=False)
                    ## # TODO: await self._verify_package("wsproxy", fat=False)
                    ## await self._verify_package("storage-proxy", fat=False)
                    ## await self._verify_package("client", fat=False)
                case PackageSource.LOCAL_DIR:
                    # Use the local files.
                    # Verify the checksums first.
                    await self._verify_package("manager", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("agent", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("agent-watcher", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("webserver", fat=self.dist_info.use_fat_binary)
                    # TODO: await self._verify_package("wsproxy", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("storage-proxy", fat=self.dist_info.use_fat_binary)
                    await self._verify_package("client", fat=self.dist_info.use_fat_binary)
                    # Copy the packages into the target path.
                    await self._install_package("manager", vpane, fat=self.dist_info.use_fat_binary)
                    await self._install_package("agent", vpane, fat=self.dist_info.use_fat_binary)
                    await self._install_package(
                        "agent-watcher", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package(
                        "webserver", vpane, fat=self.dist_info.use_fat_binary
                    )
                    # TODO: await self._install_package("wsproxy", vpane, fat=self.dist_info.use_fat_binary)
                    await self._install_package(
                        "storage-proxy", vpane, fat=self.dist_info.use_fat_binary
                    )
                    await self._install_package("client", vpane, fat=self.dist_info.use_fat_binary)
        finally:
            vpane.remove()
        await self.install_halfstack(ha_setup=False)

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
