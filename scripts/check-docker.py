import functools
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import requests
import requests_unixsocket


log = functools.partial(print, file=sys.stderr)
run = subprocess.run


def parse_version(expr):
    result = []
    for part in expr.split('.'):
        try:
            result.append(int(part))
        except ValueError:
            result.append(part)
    return tuple(result)


def detect_snap_docker():
    if not Path('/run/snapd.socket').is_socket():
        return None
    with requests.get("http+unix://%2Frun%2Fsnapd.socket/v2/snaps?names=docker") as r:
        if r.status_code != 200:
            raise RuntimeError("Failed to query Snapd package information")
        response_data = r.json()
        for pkg_data in response_data['result']:
            if pkg_data['name'] == 'docker':
                return pkg_data['version']


def detect_system_docker():
    sock_paths = [
        Path('/run/docker.sock'),      # Linux default
        Path('/var/run/docker.sock'),  # macOS default
    ]
    for sock_path in sock_paths:
        if sock_path.is_socket():
            break
    else:
        return None
    encoded_sock_path = quote(bytes(sock_path), safe='')
    with requests.get(f"http+unix://{encoded_sock_path}/version") as r:
        if r.status_code != 200:
            raise RuntimeError("Failed to query the Docker daemon API")
        response_data = r.json()
        return response_data['Version']


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


def main():
    requests_unixsocket.monkeypatch()

    docker_version = detect_snap_docker()
    if docker_version is not None:
        log(f"Detected Docker installation: Snap package ({docker_version})")
        if parse_version(docker_version) < (20, 10, 15):
            fail_with_snap_docker_refresh_request()
    else:
        docker_version = detect_system_docker()
        if docker_version is not None:
            log(f"Detected Docker installation: System package ({docker_version})")
        else:
            fail_with_system_docker_install_request()

    try:
        proc = run(['docker', 'compose', 'version'], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        fail_with_compose_install_request()
    else:
        m = re.search(r'\d+\.\d+\.\d+', proc.stdout.decode())
        if m is None:
            log("Failed to retrieve the docker-compose version!")
            sys.exit(1)
        else:
            compose_version = m.group(0)
            log(f"Detected docker-compose installation ({compose_version})")
            if parse_version(compose_version) < (2, 0, 0):
                fail_with_compose_install_request()

    # Now we can proceed with the given docker & docker-compose installation.


if __name__ == '__main__':
    main()
