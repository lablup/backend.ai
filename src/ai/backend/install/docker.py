from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
from rich.text import Text

from ai.backend.common.docker import get_docker_connector
from ai.backend.install.types import PrerequisiteError

from .http import request_unix

if TYPE_CHECKING:
    from .context import Context

__all__ = (
    "check_docker",
    "detect_snap_docker",
    "detect_system_docker",
    "determine_docker_sudo",
)


def parse_version(expr):
    result = []
    for part in expr.split("."):
        try:
            result.append(int(part))
        except ValueError:
            result.append(part)
    return tuple(result)


def get_build_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / "BUILD_ROOT").is_file():
            return p
        p = p.parent
    raise RuntimeError("Cannot determine the build root path")


def simple_hash(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(data)
    # generate a filesystem-safe base64 string
    return base64.b64encode(h.digest()[:12], altchars=b"._").decode()


async def detect_snap_docker():
    if not Path("/run/snapd.socket").is_socket():
        return None
    async with request_unix(
        "GET", "/run/snapd.socket", "http://localhost/v2/snaps?names=docker"
    ) as r:
        if r.status != 200:
            raise RuntimeError("Failed to query Snapd package information")
        response_data = await r.json()
        for pkg_data in response_data["result"]:
            if pkg_data["name"] == "docker":
                return pkg_data["version"]


async def detect_system_docker(ctx: Context) -> str:
    if ctx.docker_sudo:
        ctx.log.write(
            Text.from_markup("[yellow]Docker commands require sudo. We will use sudo.[/]")
        )
    try:
        connector = get_docker_connector()
    except RuntimeError as e:
        raise PrerequisiteError(f"Could not find the docker socket ({e})") from e
    ctx.log.write(Text.from_markup(f"[cyan]{connector=}[/]"))

    # Test a docker command to ensure passwordless sudo.
    proc = await asyncio.create_subprocess_exec(
        *(*ctx.docker_sudo, "docker", "version"),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert proc.stdout is not None
    stdout = ""
    try:
        async with asyncio.timeout(0.5):
            await proc.communicate()
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise PrerequisiteError(
            "sudo requires prompt.",
            instruction="Please make sudo available without password prompts.",
        )

    if ctx.docker_sudo:
        # Change the docker socket permission (temporarily)
        # so that we could access the docker daemon API directly.
        # NOTE: For TCP URLs (e.g., remote Docker), we don't have the socket file.
        if connector.sock_path is not None and not connector.sock_path.resolve().is_relative_to(
            Path.home()
        ):
            proc = await asyncio.create_subprocess_exec(
                *["sudo", "chmod", "666", str(connector.sock_path)],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert proc.stdout is not None
            stdout = (await proc.stdout.read()).decode()
            if (await proc.wait()) != 0:
                raise RuntimeError("Failed to set the docker socket permission", stdout)

    async with aiohttp.ClientSession(connector=connector.connector) as sess:
        async with sess.get(connector.docker_host / "version") as r:
            if r.status != 200:
                raise RuntimeError(
                    "The Docker daemon API responded with unexpected response:"
                    f" {r.status} {r.reason}"
                )
            response_data = await r.json()
            return response_data["Version"]


def fail_with_snap_docker_refresh_request() -> None:
    raise PrerequisiteError(
        "Please install Docker 20.10.15 or later from the Snap package index.",
        instruction="Try running `sudo snap refresh docker --edge`",
    )


def fail_with_system_docker_install_request() -> None:
    raise PrerequisiteError(
        "Please install Docker for your system.",
        instruction="Check out https://docs.docker.com/engine/install/",
    )


def fail_with_compose_install_request() -> None:
    raise PrerequisiteError(
        "Please install docker-compose v2 or later.",
        instruction="Check out https://docs.docker.com/compose/install/",
    )


async def get_preferred_pants_local_exec_root(ctx: Context) -> str:
    docker_version = await detect_snap_docker()
    build_root_path = get_build_root()
    build_root_name = build_root_path.name
    build_root_hash = simple_hash(os.fsencode(build_root_path))
    if docker_version is not None:
        # For Snap-based Docker, use a home directory path
        return str(Path.home() / f".cache/{build_root_name}-{build_root_hash}-pants")
    else:
        # Otherwise, use the standard tmp directory
        return f"/tmp/{build_root_name}-{build_root_hash}-pants"


async def determine_docker_sudo() -> bool:
    connector = get_docker_connector()
    try:
        async with aiohttp.ClientSession(connector=connector.connector) as sess:
            async with sess.get(connector.docker_host / "version") as r:
                await r.json()
    except ClientConnectorError as e:
        if isinstance(e.os_error, PermissionError):
            return True
        raise
    except PermissionError:
        return True
    return False


async def check_docker(ctx: Context) -> None:
    ctx.log_header("Checking Docker and Docker Compose availability")
    docker_version = await detect_snap_docker()
    if docker_version is not None:
        ctx.log.write(f"Detected Docker installation: Snap package ({docker_version})")
        if parse_version(docker_version) < (20, 10, 15):
            fail_with_snap_docker_refresh_request()
    else:
        docker_version = await detect_system_docker(ctx)
        ctx.log.write(docker_version)
        if docker_version is not None:
            ctx.log.write(f"Detected Docker installation: System package ({docker_version})")
        else:
            fail_with_system_docker_install_request()

    # Compose is not a part of the docker API but a client-side plugin.
    # We need to execute the client command to get information about it.
    proc = await asyncio.create_subprocess_exec(
        *ctx.docker_sudo, "docker", "compose", "version", stdout=asyncio.subprocess.PIPE
    )
    assert proc.stdout is not None
    stdout = await proc.stdout.read()
    exit_code = await proc.wait()
    if exit_code != 0:
        fail_with_compose_install_request()
    m = re.search(r"\d+\.\d+\.\d+", stdout.decode())
    if m is None:
        raise PrerequisiteError("Failed to retrieve the docker-compose version!")
    else:
        compose_version = m.group(0)
        ctx.log.write(f"Detected docker-compose installation ({compose_version})")
        if parse_version(compose_version) < (2, 0, 0):
            fail_with_compose_install_request()


async def check_docker_desktop_mount(ctx: Context) -> None:
    ctx.log_header("Checking Docker Desktop mount permissions")
    """
    echo "validating Docker Desktop mount permissions..."
    docker pull alpine:3.8 > /dev/null
    docker run --rm -v "$HOME/.pyenv:/root/vol" alpine:3.8 ls /root/vol > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      # backend.ai-krunner-DISTRO pkgs are installed in pyenv's virtualenv,
      # so ~/.pyenv must be mountable.
      show_error "You must allow mount of '$HOME/.pyenv' in the File Sharing preference of the Docker Desktop app."
      exit 1
    fi
    docker run --rm -v "$ROOT_PATH:/root/vol" alpine:3.8 ls /root/vol > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      show_error "You must allow mount of '$ROOT_PATH' in the File Sharing preference of the Docker Desktop app."
      exit 1
    fi
    echo "${REWRITELN}validating Docker Desktop mount permissions: ok"
    """
