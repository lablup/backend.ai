from __future__ import annotations

import contextlib
import fcntl
import hashlib
import logging
import os
import secrets
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.docker_client import DockerClient
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.minio import MinioContainer

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.testutils.pants import get_parallel_slot

# Type aliases for container fixtures
RedisContainerFixture = tuple[str, HostPortPairModel]
EtcdContainerFixture = tuple[str, HostPortPairModel]
PostgresContainerFixture = tuple[str, HostPortPairModel]
MinioContainerFixture = tuple[str, HostPortPairModel]
PrometheusContainerFixture = tuple[str, HostPortPairModel]

log = logging.getLogger(__spec__.name)

PORT_POOL_BASE: Final = int(os.environ.get("BACKEND_TEST_PORT_POOL_BASE", "10000"))
PORT_POOL_SIZE: Final = int(os.environ.get("BACKEND_TEST_PORT_POOL_SIZE", "1000"))


@contextlib.contextmanager
def sync_file_lock(path: Path, max_retries: int = 60, retry_interval: int = 2) -> Iterator[None]:
    if not path.exists():
        path.touch()
    file = path.open("wb")
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


def _wait_redis_health_check(host: str, port: int, timeout: float = 60.0) -> None:
    """Custom Redis health check using PING command (matches original implementation)."""
    deadline = time.monotonic() + timeout
    reply = b""
    while True:
        if time.monotonic() > deadline:
            raise RuntimeError(f"redis at {host}:{port} did not answer PING: {reply!r}")
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


def _flush_redis(host: str, port: int) -> None:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.connect((host, port))
        s.send(b"*1\r\n$8\r\nFLUSHALL\r\n")
        reply = s.recv(128, 0)
        if not reply.startswith(b"+OK"):
            raise RuntimeError(f"FLUSHALL on redis {host}:{port} failed: {reply!r}")


# Credentials of the pooled postgres. Distinct from halfstack's so a test can never
# reach a developer database by accident.
POSTGRES_USER: Final = "bai_testpool"
POSTGRES_PASSWORD: Final = "bai_testpool_devpass"
POSTGRES_MAINTENANCE_DB: Final = "bai_testpool"

POOL_LABEL: Final = "ai.backend.test-pool"
POOL_ROLE_LABEL: Final = "ai.backend.test-pool.role"
POOL_SLOT_LABEL: Final = "ai.backend.test-pool.slot"
SHARE_CONTAINERS_ENV: Final = "BACKEND_TEST_SHARE_CONTAINERS"
READY_TIMEOUT: Final = 60.0
# A process that finds no other holder does not remove the pool itself: Pants starts
# the next process a few seconds later and it would recreate everything. A detached
# reaper removes the pool once nobody has held it for this long.
REAP_GRACE: Final = 20.0

# Runs outside the test sandbox, so it must not import ai.backend. Waits for every
# holder to exit (a process killed by the Pants timeout releases its lock too), then
# re-checks after the grace so a process that attached meanwhile keeps the pool.
_REAPER_SCRIPT: Final = """
import fcntl, sys, time
import docker
key, lock_dir, grace = sys.argv[1], sys.argv[2], float(sys.argv[3])
reaper = open(f"{lock_dir}/reaper", "wb")
try:
    fcntl.flock(reaper.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(0)
holders = open(f"{lock_dir}/holders", "wb")
while True:
    fcntl.flock(holders.fileno(), fcntl.LOCK_EX)
    fcntl.flock(holders.fileno(), fcntl.LOCK_UN)
    time.sleep(grace)
    try:
        fcntl.flock(holders.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        break
    except BlockingIOError:
        continue
client = docker.from_env()
for c in client.containers.list(all=True, filters={"label": [f"ai.backend.test-pool={key}"]}):
    c.remove(force=True)
"""


@dataclass(frozen=True)
class PooledContainerSpec:
    role: str
    image: str
    port: int
    ready: Callable[[Any], bool]
    command: str | None = None
    environment: dict[str, str] = field(default_factory=dict)
    tmpfs: dict[str, str] = field(default_factory=dict)


class ContainerPool:
    """
    One container per (role, execution slot), kept alive across pytest processes.
    Pants runs one process per slot at a time, so a slot's containers are never shared
    concurrently. The last process alive in the checkout removes the whole pool.
    See ``tests/README.md`` for the lifecycle.
    """

    key: str
    slot: int
    shared: bool
    lock_dir: Path
    client: DockerClient
    _holders: Any
    _owned: list[Any]

    def __init__(self, key: str, slot: int, shared: bool, lock_dir: Path) -> None:
        self.key = key
        self.slot = slot
        self.shared = shared
        self.lock_dir = lock_dir
        self.client = DockerClient()
        self._owned = []
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._holders = (self.lock_dir / "holders").open("wb")
        if self.shared:
            fcntl.flock(self._holders.fileno(), fcntl.LOCK_SH)

    @classmethod
    def from_env(cls) -> ContainerPool:
        root = Path(os.environ.get("BACKEND_BUILD_ROOT", Path.cwd()))
        shared = os.environ.get(SHARE_CONTAINERS_ENV, "1") != "0"
        key = hashlib.sha1(str(root.resolve()).encode()).hexdigest()[:12]
        if not shared:
            key = f"{key}-{secrets.token_hex(4)}"
        return cls(key, get_parallel_slot(), shared, root / "tmp" / "backend.ai" / "test-pool")

    def acquire(self, spec: PooledContainerSpec) -> tuple[HostPortPairModel, bool]:
        """Return the address and whether this process created the container."""
        with sync_file_lock(self.lock_dir / f"spawn-{spec.role}-{self.slot}.lock"):
            container = self._find(spec) if self.shared else None
            created = container is None
            if container is None:
                container = self._create(spec)
                self._owned.append(container)
                self._wait_ready(container, spec)
        addr = HostPortPairModel(host="127.0.0.1", port=self._published_port(container, spec))
        return addr, created

    def release(self) -> None:
        if not self.shared:
            for container in self._owned:
                container.remove(force=True)
            self._holders.close()
            return
        fcntl.flock(self._holders.fileno(), fcntl.LOCK_UN)
        try:
            fcntl.flock(self._holders.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Another process still uses the pool; it decides when it is last.
            self._holders.close()
            return
        fcntl.flock(self._holders.fileno(), fcntl.LOCK_UN)
        self._holders.close()
        subprocess.Popen(
            [sys.executable, "-c", _REAPER_SCRIPT, self.key, str(self.lock_dir), str(REAP_GRACE)],
            cwd="/",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )

    def _list(self, *labels: str) -> list[Any]:
        return list(self.client.client.containers.list(all=True, filters={"label": list(labels)}))

    def _find(self, spec: PooledContainerSpec) -> Any | None:
        for container in self._list(
            f"{POOL_LABEL}={self.key}",
            f"{POOL_ROLE_LABEL}={spec.role}",
            f"{POOL_SLOT_LABEL}={self.slot}",
        ):
            if container.status == "running":
                log.info("reusing pooled container %s", container.name)
                return container
            log.info("removing stale pooled container %s (%s)", container.name, container.status)
            container.remove(force=True)
        return None

    def _create(self, spec: PooledContainerSpec) -> Any:
        log.info("spawning %s container (parallel slot: %d)", spec.role, self.slot)
        # Bypasses ``DockerClient.run`` so the container carries no testcontainers session
        # label: the reaper would remove it when the first process exits.
        return self.client.client.containers.run(
            spec.image,
            command=spec.command,
            detach=True,
            name=f"test-pool--{spec.role}-slot-{self.slot}-{self.key[:8]}-{secrets.token_hex(4)}",
            environment=spec.environment,
            ports={f"{spec.port}/tcp": None},
            tmpfs=spec.tmpfs,
            labels={
                POOL_LABEL: self.key,
                POOL_ROLE_LABEL: spec.role,
                POOL_SLOT_LABEL: str(self.slot),
            },
        )

    def _wait_ready(self, container: Any, spec: PooledContainerSpec) -> None:
        deadline = time.monotonic() + READY_TIMEOUT
        while not spec.ready(container):
            if time.monotonic() > deadline:
                raise RuntimeError(f"{spec.role} container {container.name} is not ready")
            time.sleep(0.1)

    def _published_port(self, container: Any, spec: PooledContainerSpec) -> int:
        container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"][f"{spec.port}/tcp"]
        return int(bindings[0]["HostPort"])


def _postgres_ready(container: Any) -> bool:
    return bool(container.exec_run(["pg_isready", "-U", POSTGRES_USER]).exit_code == 0)


def _etcd_ready(container: Any) -> bool:
    return b"ready to serve client requests" in container.logs()


def _redis_ready(container: Any) -> bool:
    return bool(container.exec_run(["redis-cli", "ping"]).exit_code == 0)


ETCD_SPEC: Final = PooledContainerSpec(
    role="etcd",
    image="quay.io/coreos/etcd:v3.5.4",
    port=2379,
    ready=_etcd_ready,
    command=(
        "/usr/local/bin/etcd "
        "-advertise-client-urls http://0.0.0.0:2379 "
        "-listen-client-urls http://0.0.0.0:2379"
    ),
    tmpfs={"/etcd-data": ""},
)

# No snapshots: a long-lived server would fail its background save and reject writes.
REDIS_SPEC: Final = PooledContainerSpec(
    role="redis",
    image="redis:7-alpine",
    port=6379,
    ready=_redis_ready,
    command='redis-server --save "" --appendonly no',
    tmpfs={"/data": ""},
)

# The image tracks the version halfstack runs, so a test exercises the same server the
# product requires.
POSTGRES_SPEC: Final = PooledContainerSpec(
    role="postgres",
    image="postgres:16.3-alpine",
    port=5432,
    ready=_postgres_ready,
    environment={
        "POSTGRES_USER": POSTGRES_USER,
        "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
        "POSTGRES_DB": POSTGRES_MAINTENANCE_DB,
    },
    tmpfs={"/var/lib/postgresql/data": ""},
)


# One pool per pytest process, shared by the three fixtures below. Conftests import the
# fixtures by name, so the pool is not a fixture itself; the last fixture to detach
# releases it.
_pool: ContainerPool | None = None
_pool_users = 0


@contextlib.contextmanager
def _pooled(spec: PooledContainerSpec) -> Iterator[tuple[HostPortPairModel, bool]]:
    global _pool, _pool_users
    if _pool is None:
        _pool = ContainerPool.from_env()
    _pool_users += 1
    try:
        yield _pool.acquire(spec)
    finally:
        _pool_users -= 1
        if _pool_users == 0:
            _pool.release()
            _pool = None


@pytest.fixture(scope="session", autouse=False)
def etcd_container() -> Iterator[tuple[str, HostPortPairModel]]:
    with _pooled(ETCD_SPEC) as (addr, created):
        if created:
            # Extra grace period to avoid intermittent connection failure
            time.sleep(0.2)
        yield addr.host, addr


@pytest.fixture(scope="session", autouse=False)
def redis_container() -> Iterator[tuple[str, HostPortPairModel]]:
    with _pooled(REDIS_SPEC) as (addr, created):
        _wait_redis_health_check(addr.host, addr.port)
        if created:
            # Extra grace period to avoid intermittent connection failure
            time.sleep(0.5)
        # The previous process in this slot leaves its keys behind.
        _flush_redis(addr.host, addr.port)
        yield addr.host, addr


@pytest.fixture(scope="session", autouse=False)
def postgres_container() -> Iterator[tuple[str, HostPortPairModel]]:
    with _pooled(POSTGRES_SPEC) as (addr, created):
        if created:
            # pg_isready answers slightly before connections are accepted
            time.sleep(0.2)
        yield addr.host, addr


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


@pytest.fixture(scope="session", autouse=False)
def prometheus_container() -> Iterator[tuple[str, HostPortPairModel]]:
    # Spawn a single-node Prometheus container for a testing session.
    random_id = secrets.token_hex(8)

    container = (
        DockerContainer("prom/prometheus:v2.53.0")
        .with_name(f"test--prometheus-slot-{get_parallel_slot()}-{random_id}")
        .with_exposed_ports(9090)
        .with_kwargs(tmpfs={"/prometheus": "rw,uid=65534,gid=65534"})
        .with_command(
            "--config.file=/etc/prometheus/prometheus.yml "
            "--storage.tsdb.path=/prometheus "
            "--storage.tsdb.retention.time=1h"
        )
    )

    log.info("spawning prometheus container (parallel slot: %d)", get_parallel_slot())
    container.start()
    published_port = int(container.get_exposed_port(9090))

    try:
        wait_for_logs(container, "Server is ready to receive web requests.")
        time.sleep(0.5)

        yield (
            container.get_container_host_ip(),
            HostPortPairModel(host="127.0.0.1", port=published_port),
        )
    finally:
        container.stop()
