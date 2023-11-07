from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .http import request_unix

if TYPE_CHECKING:
    from .context import Context

__all__ = ("check_docker",)


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


async def detect_system_docker():
    sock_paths = [
        Path("/run/docker.sock"),  # Linux default
        Path("/var/run/docker.sock"),  # macOS default
    ]
    if env_sock_path := os.environ.get("DOCKER_HOST", None):
        # Some special setups like OrbStack may have a custom DOCKER_HOST.
        env_sock_path = env_sock_path.removeprefix("unix://")
        sock_paths.insert(0, Path(env_sock_path))
    for sock_path in sock_paths:
        if sock_path.is_socket():
            break
    else:
        return None
    async with request_unix("GET", str(sock_path), "http://localhost/version") as r:
        if r.status != 200:
            raise RuntimeError("Failed to query the Docker daemon API")
        response_data = await r.json()
        return response_data["Version"]


def fail_with_snap_docker_refresh_request(log) -> None:
    log.write("Please install Docker 20.10.15 or later from the Snap package index.")
    log.write("Instructions: `sudo snap refresh docker --edge`")
    sys.exit(1)


def fail_with_system_docker_install_request(log) -> None:
    log.write("Please install Docker for your system.")
    log.write("Instructions: https://docs.docker.com/install/")
    sys.exit(1)


def fail_with_compose_install_request(log) -> None:
    log.write("Please install docker-compose v2 or later.")
    log.write("Instructions: https://docs.docker.com/compose/install/")
    sys.exit(1)


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


async def check_docker(ctx: Context) -> None:
    ctx.log_header("Checking Docker and Docker Compose availability")
    docker_version = await detect_snap_docker()
    if docker_version is not None:
        ctx.log.write(f"Detected Docker installation: Snap package ({docker_version})")
        if parse_version(docker_version) < (20, 10, 15):
            fail_with_snap_docker_refresh_request(ctx.log)
    else:
        docker_version = await detect_system_docker()
        if docker_version is not None:
            ctx.log.write(f"Detected Docker installation: System package ({docker_version})")
        else:
            fail_with_system_docker_install_request(ctx.log)

    proc = await asyncio.create_subprocess_exec(
        "docker", "compose", "version", stdout=asyncio.subprocess.PIPE
    )
    assert proc.stdout is not None
    stdout = await proc.stdout.read()
    exit_code = await proc.wait()
    if exit_code != 0:
        fail_with_compose_install_request(ctx.log)
    m = re.search(r"\d+\.\d+\.\d+", stdout.decode())
    if m is None:
        ctx.log.write("Failed to retrieve the docker-compose version!")
        sys.exit(1)
    else:
        compose_version = m.group(0)
        ctx.log.write(f"Detected docker-compose installation ({compose_version})")
        if parse_version(compose_version) < (2, 0, 0):
            fail_with_compose_install_request(ctx.log)


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
