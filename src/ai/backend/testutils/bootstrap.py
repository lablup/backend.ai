from __future__ import annotations

import contextlib
import fcntl
import json
import logging
import os
import secrets
import socket
import subprocess
import time
from pathlib import Path
from typing import Iterator

import pytest

from ai.backend.common.types import HostPortPair
from ai.backend.testutils.pants import get_parallel_slot

log = logging.getLogger(__spec__.name)  # type: ignore[name-defined]


def get_free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def check_if_port_is_clear(host, port):
    while True:
        try:
            s = socket.create_connection((host, port), timeout=0.3)
        except (ConnectionRefusedError, TimeoutError):
            break
        else:
            time.sleep(0.1)
            s.close()
            continue


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
        if not container_info:  # maybe empty if container is not yet initialized
            time.sleep(0.2)
            continue
        health_info = container_info[0]["State"].get("Health")
        if health_info is not None and health_info["Status"].lower() != "healthy":
            time.sleep(0.2)
            continue
        if health_info is None and (err_info := container_info[0]["State"].get("Error")):
            raise RuntimeError(f"Container spawn failed: {err_info}")
        # Give extra grace period to avoid intermittent connection failure.
        time.sleep(0.2)
        return container_info


@pytest.fixture(scope="session", autouse=False)
def etcd_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    etcd_allocated_port = 9600 + get_parallel_slot() * 8 + 0
    random_id = secrets.token_hex(8)
    check_if_port_is_clear("127.0.0.1", etcd_allocated_port)
    proc = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            f"test--etcd-slot-{get_parallel_slot()}-{random_id}",
            "-p",
            f"0.0.0.0:{etcd_allocated_port}:2379",
            "-p",
            "0.0.0.0::4001",
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
    if not container_id:
        raise RuntimeError("etcd_container: failed to create container", proc.stderr.decode())
    log.info("spawning etcd container on port %d", etcd_allocated_port)
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


@pytest.fixture(scope="session", autouse=False)
def redis_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    redis_allocated_port = 9600 + get_parallel_slot() * 8 + 1
    check_if_port_is_clear("127.0.0.1", redis_allocated_port)
    random_id = secrets.token_hex(8)
    proc = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "-u",
            f"{os.getuid()}:{os.getgid()}",
            "--name",
            f"test--redis-slot-{get_parallel_slot()}-{random_id}",
            "-p",
            f"0.0.0.0:{redis_allocated_port}:6379",
            # IMPORTANT: We have intentionally omitted the healthcheck here
            # to avoid intermittent failures when pausing/unpausing containers.
            "redis:7-alpine",
        ],
        capture_output=True,
    )
    container_id = proc.stdout.decode().strip()
    if not container_id:
        raise RuntimeError("redis_container: failed to create container", proc.stderr.decode())
    log.info("spawning redis container on port %d", redis_allocated_port)
    while True:
        try:
            with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.connect(("127.0.0.1", redis_allocated_port))
                s.send(b"*2\r\n$4\r\nPING\r\n$5\r\nhello\r\n")
                reply = s.recv(128, 0)
                if not reply.startswith(b"$5\r\nhello\r\n"):
                    time.sleep(0.1)
                    continue
                break
        except (ConnectionRefusedError, ConnectionResetError):
            time.sleep(0.1)
            continue
    time.sleep(0.5)
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


@pytest.fixture(scope="session", autouse=False)
def postgres_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    postgres_allocated_port = 9600 + get_parallel_slot() * 8 + 2
    check_if_port_is_clear("127.0.0.1", postgres_allocated_port)
    random_id = secrets.token_hex(8)
    proc = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            f"test--postgres-slot-{get_parallel_slot()}-{random_id}",
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
    if not container_id:
        raise RuntimeError("postgres_container: failed to create container", proc.stderr.decode())
    log.info("spawning postgres container on port %d", postgres_allocated_port)
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
