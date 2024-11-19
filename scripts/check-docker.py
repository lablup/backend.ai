import argparse
import asyncio
import base64
import functools
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import aiohttp

log = functools.partial(print, file=sys.stderr)
run = subprocess.run


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
    async with aiohttp.ClientSession(connector=aiohttp.UnixConnector("/run/snapd.socket")) as sess:
        async with sess.get("http://localhost/v2/snaps?names=docker") as r:
            try:
                r.raise_for_status()
            except:
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
    async with aiohttp.ClientSession(connector=aiohttp.UnixConnector(sock_path.as_posix())) as sess:
        async with sess.get("http://localhost/version") as r:
            try:
                r.raise_for_status()
            except:
                raise RuntimeError("Failed to query Snapd package information")
            response_data = await r.json()
            return response_data["Version"]


def fail_with_snap_docker_refresh_request():
    log("Please install Docker 20.10.15 or later from the Snap package index.")
    log("Instructions: `sudo snap refresh docker --edge`")
    sys.exit(1)


def fail_with_system_docker_install_request():
    log("Please install Docker for your system.")
    log("Instructions: https://docs.docker.com/install/")
    sys.exit(1)


def fail_with_compose_install_request():
    log("Please install docker-compose v2 or later.")
    log("Instructions: https://docs.docker.com/compose/install/")
    sys.exit(1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--get-preferred-pants-local-exec-root", action="store_true", default=False)
    args = parser.parse_args()

    if args.get_preferred_pants_local_exec_root:
        docker_version = await detect_snap_docker()
        build_root_path = get_build_root()
        build_root_name = build_root_path.name
        build_root_hash = simple_hash(os.fsencode(build_root_path))
        if docker_version is not None:
            # For Snap-based Docker, use a home directory path
            print(Path.home() / f".cache/{build_root_name}-{build_root_hash}-pants")
        else:
            # Otherwise, use the standard tmp directory
            print(f"/tmp/{build_root_name}-{build_root_hash}-pants")
        return

    docker_version = await detect_snap_docker()
    if docker_version is not None:
        log(f"Detected Docker installation: Snap package ({docker_version})")
        if parse_version(docker_version) < (20, 10, 15):
            fail_with_snap_docker_refresh_request()
    else:
        docker_version = await detect_system_docker()
        if docker_version is not None:
            log(f"Detected Docker installation: System package ({docker_version})")
        else:
            fail_with_system_docker_install_request()

    try:
        proc = run(["docker", "compose", "version"], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        fail_with_compose_install_request()
    else:
        m = re.search(r"\d+\.\d+\.\d+", proc.stdout.decode())
        if m is None:
            log("Failed to retrieve the docker-compose version!")
            sys.exit(1)
        else:
            compose_version = m.group(0)
            log(f"Detected docker-compose installation ({compose_version})")
            if parse_version(compose_version) < (2, 0, 0):
                fail_with_compose_install_request()

    # Now we can proceed with the given docker & docker-compose installation.


if __name__ == "__main__":
    asyncio.run(main())
