from __future__ import annotations

import json
import logging
import socket
import subprocess
import time
from contextlib import closing
from typing import Iterator

import pytest

from ai.backend.common.types import HostPortPair

log = logging.getLogger(__name__)


class PortNotAvailableError(Exception):
    pass


def get_idle_port(min_port_no: int, max_tries=10) -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        for port in range(min_port_no, min_port_no + max_tries):
            try:
                sock.bind(("", port))
                return port
            except OSError:
                pass
        else:
            raise PortNotAvailableError


def wait_health_check(container_id):
    while True:
        proc = subprocess.run(
            [
                "docker",
                "inspect",
                container_id,
            ],
            capture_output=True,
        )
        container_info = json.loads(proc.stdout)
        health_info = container_info[0]["State"].get("Health")
        if health_info is not None and health_info["Status"].lower() != "healthy":
            time.sleep(0.2)
            continue
        if health_info is None and (err_info := container_info[0]["State"].get("Error")):
            raise RuntimeError(f"Container spawn failed: {err_info}")
        # Give extra grace period to avoid intermittent connection failure.
        time.sleep(0.1)
        return container_info


def parse_host_port(container_id, container_port):
    proc = subprocess.run(
        [
            "docker",
            "inspect",
            container_id,
        ],
        capture_output=True,
    )
    container_info = json.loads(proc.stdout)
    return int(
        container_info[0]["NetworkSettings"]["Ports"][f"{container_port}/tcp"][0]["HostPort"]
    )


@pytest.fixture(scope="session")
def etcd_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    etcd_allocated_port = get_idle_port(12379)
    log.info("spawning etcd container on port {}", etcd_allocated_port)
    proc = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "-p",
            f"0.0.0.0:{etcd_allocated_port}:2379",
            "-p",
            ":4001",
            "--health-cmd",
            "etcdctl endpoint health",
            "--health-interval",
            "2s",
            "--health-start-period",
            "1s",
            "quay.io/coreos/etcd:v3.5.4",
            "/usr/local/bin/etcd",
            "-advertise-client-urls",
            "http://0.0.0.0:2379",
            "-listen-client-urls",
            "http://0.0.0.0:2379",
        ],
        capture_output=True,
    )
    container_id = proc.stdout.decode().strip()
    wait_health_check(container_id)
    yield container_id, HostPortPair("127.0.0.1", etcd_allocated_port)
    subprocess.run(
        [
            "docker",
            "rm",
            "-v",
            "-f",
            container_id,
        ],
        capture_output=True,
    )


@pytest.fixture(scope="session")
def redis_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    redis_allocated_port = get_idle_port(16379)
    log.info("spawning redis container on port {}", redis_allocated_port)
    proc = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--health-cmd",
            "redis-cli ping | grep PONG",
            "-p",
            f"0.0.0.0:{redis_allocated_port}:6379",
            "--health-interval",
            "1s",
            "--health-start-period",
            "0.3s",
            "redis:7-alpine",
        ],
        capture_output=True,
    )
    container_id = proc.stdout.decode().strip()
    wait_health_check(container_id)
    yield container_id, HostPortPair("127.0.0.1", redis_allocated_port)
    subprocess.run(
        [
            "docker",
            "rm",
            "-v",
            "-f",
            container_id,
        ],
        capture_output=True,
    )


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    postgres_allocated_port = get_idle_port(15432)
    log.info("spawning postgres container on port {}", postgres_allocated_port)
    proc = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "-p",
            f"0.0.0.0:{postgres_allocated_port}:5432",
            "-e",
            "POSTGRES_PASSWORD=develove",
            "-e",
            "POSTGRES_DB=testing",
            "--health-cmd",
            "pg_isready -U postgres",
            "--health-interval",
            "1s",
            "--health-start-period",
            "2s",
            "postgres:13.6-alpine",
        ],
        capture_output=True,
    )
    container_id = proc.stdout.decode().strip()
    wait_health_check(container_id)
    yield container_id, HostPortPair("127.0.0.1", postgres_allocated_port)
    subprocess.run(
        [
            "docker",
            "rm",
            "-v",
            "-f",
            container_id,
        ],
        capture_output=True,
    )
