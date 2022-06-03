from __future__ import annotations

import json
import subprocess
import time
from typing import (
    Iterator,
)

import pytest

from ai.backend.common.types import HostPortPair


@pytest.fixture(scope='session')
def etcd_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    proc = subprocess.run(
        [
            'docker', 'run', '-d',
            '-p', ':2379',
            '-p', ':4001',
            'quay.io/coreos/etcd:v3.5.4',
            '/usr/local/bin/etcd',
            '-advertise-client-urls', 'http://0.0.0.0:2379',
            '-listen-client-urls', 'http://0.0.0.0:2379',
        ],
        capture_output=True,
    )
    container_id = proc.stdout.decode().strip()
    proc = subprocess.run(
        [
            'docker', 'inspect', container_id,
        ],
        capture_output=True,
    )
    container_info = json.loads(proc.stdout)
    host_port = int(container_info[0]['NetworkSettings']['Ports']['2379/tcp'][0]['HostPort'])
    yield container_id, HostPortPair('127.0.0.1', host_port)
    subprocess.run(
        [
            'docker', 'rm', '-v', '-f', container_id,
        ],
        capture_output=True,
    )


@pytest.fixture(scope='session')
def redis_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    proc = subprocess.run(
        [
            'docker', 'run', '-d',
            '-p', ':6379',
            'redis:6.2-alpine',
        ],
        capture_output=True,
    )
    container_id = proc.stdout.decode().strip()
    proc = subprocess.run(
        [
            'docker', 'inspect', container_id,
        ],
        capture_output=True,
    )
    container_info = json.loads(proc.stdout)
    host_port = int(container_info[0]['NetworkSettings']['Ports']['6379/tcp'][0]['HostPort'])
    yield container_id, HostPortPair('127.0.0.1', host_port)
    subprocess.run(
        [
            'docker', 'rm', '-v', '-f', container_id,
        ],
        capture_output=True,
    )


@pytest.fixture(scope='session')
def postgres_container() -> Iterator[tuple[str, HostPortPair]]:
    # Spawn a single-node etcd container for a testing session.
    proc = subprocess.run(
        [
            'docker', 'run', '-d',
            '-p', ':5432',
            '-e', 'POSTGRES_PASSWORD=develove',
            '-e', 'POSTGRES_DB=testing',
            '--health-cmd', 'pg_isready -U postgres',
            '--health-interval', '1s',
            '--health-start-period', '2s',
            'postgres:13.6-alpine',
        ],
        capture_output=True,
    )
    container_id = proc.stdout.decode().strip()
    host_port = 0
    while host_port == 0:
        proc = subprocess.run(
            [
                'docker', 'inspect', container_id,
            ],
            capture_output=True,
        )
        container_info = json.loads(proc.stdout)
        if container_info[0]['State']['Health']['Status'].lower() != 'healthy':
            time.sleep(0.2)
            continue
        host_port = int(container_info[0]['NetworkSettings']['Ports']['5432/tcp'][0]['HostPort'])
    yield container_id, HostPortPair('127.0.0.1', host_port)
    subprocess.run(
        [
            'docker', 'rm', '-v', '-f', container_id,
        ],
        capture_output=True,
    )
