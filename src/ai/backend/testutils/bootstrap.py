from __future__ import annotations

import contextlib
import fcntl
import logging
import os
import secrets
import socket
import time
from pathlib import Path
from typing import Final, Iterator

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.minio import MinioContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.testutils.pants import get_parallel_slot

log = logging.getLogger(__spec__.name)

PORT_POOL_BASE: Final = int(os.environ.get("BACKEND_TEST_PORT_POOL_BASE", "10000"))
PORT_POOL_SIZE: Final = int(os.environ.get("BACKEND_TEST_PORT_POOL_SIZE", "1000"))


@contextlib.contextmanager
def sync_file_lock(path: Path, max_retries: int = 60, retry_interval: int = 2):
    if not path.exists():
        path.touch()
    file = open(path, "wb")
    acquired = False
    try:
        for _ in range(max_retries):
            try:
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                yield
                break
            except BlockingIOError:
                log.exception("error while trying to acquire filelock")
                time.sleep(retry_interval)
        if not acquired:
            raise RuntimeError(f"failed to acquire filelock from path {path}")
    finally:
        if acquired:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        file.close()


def _wait_redis_health_check(host: str, port: int) -> None:
    """Custom Redis health check using PING command (matches original implementation)."""
    while True:
        try:
            with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.connect((host, port))
                s.send(b"*2\r\n$4\r\nPING\r\n$5\r\nhello\r\n")
                reply = s.recv(128, 0)
                if not reply.startswith(b"$5\r\nhello\r\n"):
                    time.sleep(0.1)
                    continue
                break
        except (ConnectionRefusedError, ConnectionResetError):
            time.sleep(0.1)
            continue
    # Extra grace period to avoid intermittent connection failure
    time.sleep(0.5)


@pytest.fixture(scope="session", autouse=False)
def etcd_container() -> Iterator[tuple[str, HostPortPairModel]]:
    # Spawn a single-node etcd container for a testing session.
    random_id = secrets.token_hex(8)

    container = (
        DockerContainer("quay.io/coreos/etcd:v3.5.4")
        .with_name(f"test--etcd-slot-{get_parallel_slot()}-{random_id}")
        .with_exposed_ports(2379)
        .with_kwargs(tmpfs={"/etcd-data": ""})
        .with_command(
            "/usr/local/bin/etcd "
            "-advertise-client-urls http://0.0.0.0:2379 "
            "-listen-client-urls http://0.0.0.0:2379"
        )
    )

    log.info("spawning etcd container (parallel slot: %d)", get_parallel_slot())
    container.start()
    published_port = int(container.get_exposed_port(2379))

    try:
        # Wait for etcd to be ready using log message
        wait_for_logs(container, "ready to serve client requests")
        # Extra grace period to avoid intermittent connection failure
        time.sleep(0.2)

        yield (
            container.get_container_host_ip(),
            HostPortPairModel(host="127.0.0.1", port=published_port),
        )
    finally:
        container.stop()


@pytest.fixture(scope="session", autouse=False)
def redis_container() -> Iterator[tuple[str, HostPortPairModel]]:
    # Spawn a single-node redis container for a testing session.
    random_id = secrets.token_hex(8)
    # IMPORTANT: We intentionally use custom health check instead of Docker's
    # built-in health check to avoid intermittent failures when pausing/unpausing containers.
    container = (
        RedisContainer("redis:7-alpine")
        .with_name(f"test--redis-slot-{get_parallel_slot()}-{random_id}")
        .with_exposed_ports(6379)
        .with_kwargs(tmpfs={"/data": ""}, user=f"{os.getuid()}:{os.getgid()}")
    )

    log.info("spawning redis container (parallel slot: %d)", get_parallel_slot())
    container.start()
    published_port = int(container.get_exposed_port(6379))

    try:
        # Use custom PING health check (matches original implementation)
        _wait_redis_health_check("127.0.0.1", published_port)

        yield (
            container.get_container_host_ip(),
            HostPortPairModel(host="127.0.0.1", port=published_port),
        )
    finally:
        container.stop()


@pytest.fixture(scope="session", autouse=False)
def postgres_container() -> Iterator[tuple[str, HostPortPairModel]]:
    # Spawn a single-node PostgreSQL container for a testing session.
    random_id = secrets.token_hex(8)
    container = (
        PostgresContainer(
            "postgres:13.6-alpine", username="postgres", password="develove", dbname="testing"
        )
        .with_name(f"test--postgres-slot-{get_parallel_slot()}-{random_id}")
        .with_exposed_ports(5432)
        .with_kwargs(tmpfs={"/var/lib/postgresql/data": ""})
    )

    log.info("spawning postgres container (parallel slot: %d)", get_parallel_slot())
    container.start()
    published_port = int(container.get_exposed_port(5432))

    try:
        # PostgresContainer automatically waits for pg_isready, but add grace period
        time.sleep(0.2)

        yield (
            container.get_container_host_ip(),
            HostPortPairModel(host="127.0.0.1", port=published_port),
        )
    finally:
        container.stop()


@pytest.fixture(scope="session", autouse=False)
def minio_container() -> Iterator[tuple[str, HostPortPairModel]]:
    # Spawn a single-node MinIO container for a testing session.
    random_id = secrets.token_hex(8)

    container = (
        MinioContainer("minio/minio:latest", access_key="minioadmin", secret_key="minioadmin")
        .with_name(f"test--minio-slot-{get_parallel_slot()}-{random_id}")
        .with_exposed_ports(9000)
        .with_exposed_ports(9090)
        .with_kwargs(tmpfs={"/data": ""})
        .with_command("server /data --console-address :9090")
    )

    log.info("spawning minio container (parallel slot: %d)", get_parallel_slot())
    container.start()
    api_port = int(container.get_exposed_port(9000))
    _ = int(container.get_exposed_port(9090))

    try:
        # MinioContainer automatically waits for MinIO to be ready, but add grace period
        time.sleep(0.2)

        yield container.get_container_host_ip(), HostPortPairModel(host="127.0.0.1", port=api_port)
    finally:
        container.stop()
