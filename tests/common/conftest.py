import asyncio
import secrets
import time
from decimal import Decimal

import pytest

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.testutils.bootstrap import (  # noqa: F401
    etcd_container,
    redis_container,
    sync_file_lock,
)


def pytest_addoption(parser):
    parser.addoption(
        "--skip-test-redis",
        action="store_true",
        default=False,
        help="run Redis tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "redis: mark test as part of Redis test suite")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-test-redis"):
        # auto-skip tests marked with "redis" unless --test-redis option is given.
        do_skip = pytest.mark.skip(
            reason="skipped because no related files are changed",
        )
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(do_skip)


@pytest.fixture(scope="session", autouse=True)
def test_ns():
    return f"test-{secrets.token_hex(8)}"


@pytest.fixture
def test_case_ns():
    return secrets.token_hex(8)


@pytest.fixture
async def etcd(etcd_container, test_ns):  # noqa: F811
    etcd = AsyncEtcd(
        addr=etcd_container[1],
        namespace=test_ns,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/testing",
            ConfigScopes.NODE: "node/i-test",
        },
    )
    try:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        yield etcd
    finally:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        await etcd.delete_prefix("", scope=ConfigScopes.SGROUP)
        await etcd.delete_prefix("", scope=ConfigScopes.NODE)
        await etcd.close()
        del etcd


@pytest.fixture
async def gateway_etcd(etcd_container, test_ns):  # noqa: F811
    etcd = AsyncEtcd(
        addr=etcd_container[1],
        namespace=test_ns,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "",
        },
    )
    try:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        yield etcd
    finally:
        await etcd.delete_prefix("", scope=ConfigScopes.GLOBAL)
        del etcd


@pytest.fixture
async def chaos_generator():
    async def _chaos():
        try:
            while True:
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            return

    tasks = []
    for i in range(20):
        tasks.append(asyncio.create_task(_chaos()))
    yield
    for i in range(20):
        tasks[i].cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.fixture
def mock_time(mocker):
    total_delay = Decimal(0)
    call_count = 0
    base_time = time.monotonic()
    accum_time = Decimal(0)
    q = Decimal(".000000")

    async def _mock_async_sleep(delay: float) -> None:
        nonlocal total_delay, call_count, accum_time, q
        call_count += 1
        quantized_delay = Decimal(delay).quantize(q)
        accum_time += quantized_delay
        total_delay += quantized_delay

    def _reset() -> None:
        nonlocal total_delay, call_count
        total_delay = Decimal(0)
        call_count = 0

    def _get_total_delay() -> float:
        nonlocal total_delay
        return float(total_delay)

    def _get_call_count() -> int:
        nonlocal call_count
        return call_count

    def _mock_time_monotonic() -> float:
        nonlocal accum_time
        return base_time + float(accum_time)

    _mock_async_sleep.reset = _reset
    _mock_async_sleep.get_total_delay = _get_total_delay
    _mock_async_sleep.get_call_count = _get_call_count
    yield _mock_async_sleep, _mock_time_monotonic


@pytest.fixture
def allow_and_block_list():
    return {"cuda"}, {"cuda_mock"}


@pytest.fixture
def allow_and_block_list_has_union():
    return {"cuda"}, {"cuda"}
