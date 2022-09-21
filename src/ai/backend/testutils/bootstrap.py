from __future__ import annotations

import json
import logging
import subprocess
import time
from typing import Iterator

import pytest

from ai.backend.common.types import HostPortPair
from ai.backend.testutils.pants import get_parallel_slot

log = logging.getLogger(__name__)


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


@pytest.fixture(scope="session")
def etcd_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    etcd_allocated_port = 12379 + get_parallel_slot() * 10
    log.info("spawning etcd container on port %d", etcd_allocated_port)
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
    redis_allocated_port = 36379 + get_parallel_slot() * 10
    log.info("spawning redis container on port %d", redis_allocated_port)
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
    postgres_allocated_port = 15432 + get_parallel_slot() * 10
    log.info("spawning postgres container on port %d", postgres_allocated_port)
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
