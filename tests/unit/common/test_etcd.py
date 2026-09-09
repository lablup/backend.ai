from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from etcd_client import ClientError, CondVar, GRPCStatusCode, GRPCStatusError, WatchEventType

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes, Event
from ai.backend.common.lock import EtcdLock
from ai.backend.common.types import HostPortPair, QueueSentinel


async def test_basic_crud(etcd: AsyncEtcd) -> None:
    await etcd.put("wow", "abc")

    v = await etcd.get("wow")
    assert v == "abc"
    vp = await etcd.get_prefix("wow")
    assert len(vp) == 1
    assert vp == {"": "abc"}

    r = await etcd.replace("wow", "aaa", "ccc")
    assert r is False
    r = await etcd.replace("wow", "abc", "def")
    assert r is True
    v = await etcd.get("wow")
    assert v == "def"

    await etcd.delete("wow")

    v = await etcd.get("wow")
    assert v is None
    vp = await etcd.get_prefix("wow")
    assert len(vp) == 0


async def test_put_if_absent_has_one_winner_on_real_etcd(etcd: AsyncEtcd) -> None:
    results = await asyncio.gather(*(etcd.put_if_absent("cas/key", str(i)) for i in range(16)))

    assert results.count(True) == 1
    assert await etcd.get("cas/key", scope=ConfigScopes.GLOBAL) in {str(i) for i in range(16)}


async def test_compare_and_put_checks_target_and_guards_atomically(etcd: AsyncEtcd) -> None:
    await etcd.put("cas/target", "old")
    await etcd.put("cas/guard", "generation-1")

    assert await etcd.compare_and_put(
        "cas/target",
        "new",
        expected="old",
        guards={"cas/guard": "generation-1", "cas/absent": None},
    )
    await etcd.put("cas/guard", "generation-2")

    assert not await etcd.compare_and_put(
        "cas/target",
        "wrong",
        expected="new",
        guards={"cas/guard": "generation-1"},
    )
    assert await etcd.get("cas/target", scope=ConfigScopes.GLOBAL) == "new"


async def test_compare_and_delete_preserves_a_value_when_a_guard_moves(etcd: AsyncEtcd) -> None:
    await etcd.put("cas/claim", "owner-1")
    await etcd.put("cas/guard", "generation-2")

    assert not await etcd.compare_and_delete(
        "cas/claim",
        "owner-1",
        guards={"cas/guard": "generation-1"},
    )
    assert await etcd.get("cas/claim", scope=ConfigScopes.GLOBAL) == "owner-1"


async def test_iter_prefix_pages_over_one_revision(etcd: AsyncEtcd) -> None:
    for index in range(7):
        await etcd.put(f"paged/{index}", f"value-{index}")

    iterator = etcd.iter_prefix("paged", page_size=2)
    first_page = [await anext(iterator), await anext(iterator)]
    await etcd.put("paged/9", "written-after-the-snapshot")
    remaining = [item async for item in iterator]

    assert first_page + remaining == [(f"paged/{index}", f"value-{index}") for index in range(7)]


async def test_iter_prefix_keeps_scope_prefixes_internal(etcd: AsyncEtcd) -> None:
    await etcd.put("paged/global", "global", scope=ConfigScopes.GLOBAL)
    await etcd.put("paged/node", "node", scope=ConfigScopes.NODE)

    items = [
        item
        async for item in etcd.iter_prefix(
            "paged",
            scope=ConfigScopes.GLOBAL,
            page_size=1,
        )
    ]

    assert items == [("paged/global", "global")]


async def test_etcd_lease_lock_allows_one_holder_and_releases_on_exit(
    etcd: AsyncEtcd, test_case_ns: str
) -> None:
    acquired = asyncio.Event()
    release = asyncio.Event()
    lock_name = f"tests/reconcile/{test_case_ns}"

    async def hold() -> None:
        async with EtcdLock(lock_name, etcd, timeout=1, lifetime=2):
            acquired.set()
            await release.wait()

    holder = asyncio.create_task(hold())
    await acquired.wait()
    with pytest.raises(ClientError):
        async with EtcdLock(lock_name, etcd, timeout=0.05, lifetime=2):
            pytest.fail("two managers acquired one reconciliation lease")

    release.set()
    await holder
    async with EtcdLock(lock_name, etcd, timeout=1, lifetime=2):
        pass


async def test_etcd_lease_lock_renews_while_the_reconciler_holds_it(
    etcd: AsyncEtcd, test_case_ns: str
) -> None:
    acquired = asyncio.Event()
    release = asyncio.Event()
    lock_name = f"tests/reconcile-renewal/{test_case_ns}"

    async def hold_past_ttl() -> None:
        async with EtcdLock(lock_name, etcd, timeout=1, lifetime=1):
            acquired.set()
            await release.wait()

    holder = asyncio.create_task(hold_past_ttl())
    await acquired.wait()
    await asyncio.sleep(1.5)
    with pytest.raises(ClientError):
        async with EtcdLock(lock_name, etcd, timeout=0.05, lifetime=1):
            pytest.fail("the reconciliation lease expired while its leader was still running")

    release.set()
    await holder


async def test_quote_for_put_prefix(etcd: AsyncEtcd) -> None:
    await etcd.put_prefix(
        "data",
        {
            "aa:bb": {
                "option1": "value1",
                "option2": "value2",
                "myhost/path": "this",
            },
            "aa:cc": "wow",
            "aa:dd": {
                "": "oops",
            },
        },
        scope=ConfigScopes.GLOBAL,
    )
    v = await etcd.get("data/aa%3Abb/option1")
    assert v == "value1"
    v = await etcd.get("data/aa%3Abb/option2")
    assert v == "value2"
    v = await etcd.get("data/aa%3Abb/myhost%2Fpath")
    assert v == "this"
    v = await etcd.get("data/aa%3Acc")
    assert v == "wow"
    v = await etcd.get("data/aa%3Add")
    assert v == "oops"


async def test_unquote_for_get_prefix(etcd: AsyncEtcd) -> None:
    await etcd.put("obj/aa%3Abb/option1", "value1")
    await etcd.put("obj/aa%3Abb/option2", "value2")
    await etcd.put("obj/aa%3Abb/myhost%2Fpath", "this")
    await etcd.put("obj/aa%3Acc", "wow")

    v = await etcd.get_prefix("obj")
    assert dict(v) == {
        "aa:bb": {
            "option1": "value1",
            "option2": "value2",
            "myhost/path": "this",
        },
        "aa:cc": "wow",
    }

    v = await etcd.get_prefix("obj/aa%3Abb")
    assert dict(v) == {
        "option1": "value1",
        "option2": "value2",
        "myhost/path": "this",
    }

    v = await etcd.get_prefix("obj/aa%3Acc")
    assert dict(v) == {"": "wow"}


async def test_scope_empty_prefix(gateway_etcd: AsyncEtcd) -> None:
    # This test case is to ensure compatibility with the legacy managers.
    # gateway_etcd is created with a scope prefix map that contains
    # ConfigScopes.GLOBAL => ''
    # setting so that global scope configurations have the same key
    # used before introduction of scoped configurations.
    await gateway_etcd.put("wow", "abc")
    v = await gateway_etcd.get("wow")
    assert v == "abc"

    vp = await gateway_etcd.get_prefix("wow")
    assert len(vp) == 1
    assert vp == {"": "abc"}

    r = await gateway_etcd.replace("wow", "aaa", "ccc")
    assert r is False
    r = await gateway_etcd.replace("wow", "abc", "def")
    assert r is True
    v = await gateway_etcd.get("wow")
    assert v == "def"

    await gateway_etcd.delete("wow")

    v = await gateway_etcd.get("wow")
    assert v is None
    vp = await gateway_etcd.get_prefix("wow")
    assert len(vp) == 0


async def test_scope(etcd: AsyncEtcd) -> None:
    await etcd.put("wow", "abc", scope=ConfigScopes.GLOBAL)
    await etcd.put("wow", "def", scope=ConfigScopes.SGROUP)
    await etcd.put("wow", "ghi", scope=ConfigScopes.NODE)
    v = await etcd.get("wow")
    assert v == "ghi"

    await etcd.delete("wow", scope=ConfigScopes.NODE)
    v = await etcd.get("wow")
    assert v == "def"

    await etcd.delete("wow", scope=ConfigScopes.SGROUP)
    v = await etcd.get("wow")
    assert v == "abc"

    await etcd.delete("wow", scope=ConfigScopes.GLOBAL)
    v = await etcd.get("wow")
    assert v is None

    await etcd.put("wow", "000", scope=ConfigScopes.NODE)
    v = await etcd.get("wow")
    assert v == "000"


async def test_scope_dict(etcd: AsyncEtcd) -> None:
    await etcd.put_dict({"point/x": "1", "point/y": "2"}, scope=ConfigScopes.GLOBAL)
    await etcd.put_dict({"point/y": "3"}, scope=ConfigScopes.SGROUP)
    await etcd.put_dict({"point/x": "4", "point/z": "5"}, scope=ConfigScopes.NODE)
    vp = await etcd.get_prefix("point", scope=ConfigScopes.MERGED)
    assert vp == {"x": "4", "y": "3", "z": "5"}
    vp = await etcd.get_prefix("point", scope=ConfigScopes.SGROUP)
    assert vp == {"x": "1", "y": "3"}
    vp = await etcd.get_prefix("point", scope=ConfigScopes.GLOBAL)
    assert vp == {"x": "1", "y": "2"}

    await etcd.delete_prefix("point", scope=ConfigScopes.NODE)
    vp = await etcd.get_prefix("point", scope=ConfigScopes.MERGED)
    assert vp == {"x": "1", "y": "3"}

    await etcd.delete_prefix("point", scope=ConfigScopes.SGROUP)
    vp = await etcd.get_prefix("point", scope=ConfigScopes.MERGED)
    assert vp == {"x": "1", "y": "2"}

    await etcd.delete_prefix("point", scope=ConfigScopes.GLOBAL)
    vp = await etcd.get_prefix("point", scope=ConfigScopes.MERGED)
    assert len(vp) == 0


async def test_multi(etcd: AsyncEtcd) -> None:
    v = await etcd.get("foo")
    assert v is None
    v = await etcd.get("bar")
    assert v is None

    await etcd.put_dict({"foo": "x", "bar": "y"})
    v = await etcd.get("foo")
    assert v == "x"
    v = await etcd.get("bar")
    assert v == "y"

    await etcd.delete_multi(["foo", "bar"])
    v = await etcd.get("foo")
    assert v is None
    v = await etcd.get("bar")
    assert v is None


async def test_atomic_replace_prefixes_swaps_subtree(etcd: AsyncEtcd) -> None:
    await etcd.put_prefix(
        "svc/bai_service_a",
        {"loadBalancer": {"servers": {"0": {"url": "old0"}, "1": {"url": "old1"}}}},
    )

    # Shrink from two servers to one: the stale servers/1 key must be dropped.
    await etcd.atomic_replace_prefixes({
        "svc/bai_service_a": {"loadBalancer": {"servers": {"0": {"url": "new0"}}}},
    })

    vp = await etcd.get_prefix("svc/bai_service_a")
    assert vp == {"loadBalancer": {"servers": {"0": {"url": "new0"}}}}


async def test_atomic_replace_prefixes_empty_removes_subtree(etcd: AsyncEtcd) -> None:
    await etcd.put_prefix(
        "svc/bai_service_b",
        {"loadBalancer": {"servers": {"0": {"url": "u0"}}}},
    )

    await etcd.atomic_replace_prefixes({"svc/bai_service_b": {}})

    vp = await etcd.get_prefix("svc/bai_service_b")
    assert len(vp) == 0


async def test_atomic_replace_prefixes_isolates_siblings(etcd: AsyncEtcd) -> None:
    await etcd.put_prefix("svc/bai_service_c", {"loadBalancer": {"servers": {"0": {"url": "c0"}}}})
    await etcd.put_prefix("svc/bai_service_d", {"loadBalancer": {"servers": {"0": {"url": "d0"}}}})

    # Replacing one circuit's subtree must not touch its sibling under the same parent.
    await etcd.atomic_replace_prefixes({
        "svc/bai_service_c": {"loadBalancer": {"servers": {"0": {"url": "c0-new"}}}},
    })

    vc = await etcd.get_prefix("svc/bai_service_c")
    assert vc == {"loadBalancer": {"servers": {"0": {"url": "c0-new"}}}}
    vd = await etcd.get_prefix("svc/bai_service_d")
    assert vd == {"loadBalancer": {"servers": {"0": {"url": "d0"}}}}


async def test_atomic_replace_prefixes_multiple_subtrees(etcd: AsyncEtcd) -> None:
    await etcd.put_prefix("cfg/routers/bai_router_e", {"rule": "old-rule"})
    await etcd.put_prefix("cfg/services/bai_service_e", {"loadBalancer": {"servers": {"0": "old"}}})

    await etcd.atomic_replace_prefixes({
        "cfg/routers/bai_router_e": {"rule": "new-rule", "service": "bai_service_e"},
        "cfg/services/bai_service_e": {"loadBalancer": {"servers": {"0": "new"}}},
    })

    assert await etcd.get_prefix("cfg/routers/bai_router_e") == {
        "rule": "new-rule",
        "service": "bai_service_e",
    }
    assert await etcd.get_prefix("cfg/services/bai_service_e") == {
        "loadBalancer": {"servers": {"0": "new"}}
    }


async def test_watch(etcd: AsyncEtcd) -> None:
    records = []
    records_prefix = []
    r_ready = CondVar()
    rp_ready = CondVar()

    async def _record() -> None:
        recv_count = 0
        async for ev in etcd.watch("wow", ready_event=r_ready):
            if not isinstance(ev, QueueSentinel):
                records.append(ev)
                recv_count += 1
                if recv_count == 2:
                    return

    async def _record_prefix() -> None:
        recv_count = 0
        async for ev in etcd.watch_prefix("wow", ready_event=rp_ready):
            if not isinstance(ev, QueueSentinel):
                records_prefix.append(ev)
                recv_count += 1
                if recv_count == 4:
                    return

    async with (
        asyncio.timeout(10),
        asyncio.TaskGroup() as tg,
    ):
        tg.create_task(_record())
        tg.create_task(_record_prefix())

        await r_ready.wait()
        await rp_ready.wait()

        await etcd.put("wow", "123")
        await etcd.delete("wow")
        await etcd.put("wow/child", "hello")
        await etcd.delete_prefix("wow")

    assert records[0].key == "wow"
    assert records[0].event == WatchEventType.PUT
    assert records[0].value == "123"
    assert records[1].key == "wow"
    assert records[1].event == WatchEventType.DELETE
    assert records[1].value == ""

    assert records_prefix[0].key == "wow"
    assert records_prefix[0].event == WatchEventType.PUT
    assert records_prefix[0].value == "123"
    assert records_prefix[1].key == "wow"
    assert records_prefix[1].event == WatchEventType.DELETE
    assert records_prefix[1].value == ""
    assert records_prefix[2].key == "wow/child"
    assert records_prefix[2].event == WatchEventType.PUT
    assert records_prefix[2].value == "hello"
    assert records_prefix[3].key == "wow/child"
    assert records_prefix[3].event == WatchEventType.DELETE
    assert records_prefix[3].value == ""


async def test_watch_once(etcd: AsyncEtcd) -> None:
    records = []
    records_prefix = []
    r_ready = CondVar()
    rp_ready = CondVar()

    async def _record() -> None:
        recv_count = 0
        async for ev in etcd.watch("wow", once=True, ready_event=r_ready):
            if not isinstance(ev, QueueSentinel):
                records.append(ev)
                recv_count += 1
                if recv_count == 1:
                    return

    async def _record_prefix() -> None:
        recv_count = 0
        async for ev in etcd.watch_prefix("wow/city", once=True, ready_event=rp_ready):
            if not isinstance(ev, QueueSentinel):
                records_prefix.append(ev)
                recv_count += 1
                if recv_count == 1:
                    return

    async with (
        asyncio.timeout(10),
        asyncio.TaskGroup() as tg,
    ):
        tg.create_task(_record())
        tg.create_task(_record_prefix())

        await r_ready.wait()
        await rp_ready.wait()

        await etcd.put("wow/city1", "seoul")
        await etcd.put("wow/city2", "daejeon")
        await etcd.put("wow", "korea")
        await etcd.delete_prefix("wow")

    assert records[0].key == "wow"
    assert records[0].event == WatchEventType.PUT
    assert records[0].value == "korea"

    assert records_prefix[0].key == "wow/city1"
    assert records_prefix[0].event == WatchEventType.PUT
    assert records_prefix[0].value == "seoul"


class TestWatchExponentialBackoff:
    """Unit tests for exponential backoff in watch() and watch_prefix()."""

    @pytest.fixture
    def etcd(self) -> AsyncEtcd:
        return AsyncEtcd(
            addrs=HostPortPair("127.0.0.1", 2379),
            namespace="test-backoff",
            scope_prefix_map={ConfigScopes.GLOBAL: ""},
            watch_reconnect_intvl=0.5,
            watch_reconnect_max_intvl=30.0,
        )

    def _unavail_err(self) -> GRPCStatusError:
        return GRPCStatusError({"code": GRPCStatusCode.Unavailable})

    def test_calc_delay_progression(self, etcd: AsyncEtcd) -> None:
        """_calc_watch_reconnect_delay doubles the delay on each attempt."""
        assert etcd._calc_watch_reconnect_delay(1) == pytest.approx(0.5)
        assert etcd._calc_watch_reconnect_delay(2) == pytest.approx(1.0)
        assert etcd._calc_watch_reconnect_delay(3) == pytest.approx(2.0)
        assert etcd._calc_watch_reconnect_delay(4) == pytest.approx(4.0)
        assert etcd._calc_watch_reconnect_delay(5) == pytest.approx(8.0)

    def test_calc_delay_cap(self) -> None:
        """_calc_watch_reconnect_delay is bounded by watch_reconnect_max_intvl."""
        bounded = AsyncEtcd(
            addrs=HostPortPair("127.0.0.1", 2379),
            namespace="test-cap",
            scope_prefix_map={ConfigScopes.GLOBAL: ""},
            watch_reconnect_intvl=0.5,
            watch_reconnect_max_intvl=10.0,
        )
        # 0.5 * 2^4 = 8.0  (below cap)
        assert bounded._calc_watch_reconnect_delay(5) == pytest.approx(8.0)
        # 0.5 * 2^5 = 16.0 → capped at 10.0
        assert bounded._calc_watch_reconnect_delay(6) == pytest.approx(10.0)
        # Always capped beyond this point
        assert bounded._calc_watch_reconnect_delay(10) == pytest.approx(10.0)

    async def test_watch_exponential_backoff_increases_delay(self, etcd: AsyncEtcd) -> None:
        """watch() sleeps with exponentially increasing delays on Unavailable errors."""
        n_failures = 4
        call_count = 0
        err = self._unavail_err()

        async def mock_watch_impl(*args: Any, **kwargs: Any) -> AsyncGenerator[Event, None]:
            nonlocal call_count
            call_count += 1
            if call_count <= n_failures:
                raise err
            empty: list[Event] = []
            for ev in empty:
                yield ev

        with (
            patch.object(etcd, "_watch_impl", new=mock_watch_impl),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            async for _ in etcd.watch("test-key"):
                pass

        assert mock_sleep.call_count == n_failures
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == pytest.approx([0.5, 1.0, 2.0, 4.0])

    async def test_watch_backoff_caps_at_max(self, etcd: AsyncEtcd) -> None:
        """watch() sleep delay never exceeds watch_reconnect_max_intvl (30 s)."""
        n_failures = 8
        call_count = 0
        err = self._unavail_err()

        async def mock_watch_impl(*args: Any, **kwargs: Any) -> AsyncGenerator[Event, None]:
            nonlocal call_count
            call_count += 1
            if call_count <= n_failures:
                raise err
            empty: list[Event] = []
            for ev in empty:
                yield ev

        with (
            patch.object(etcd, "_watch_impl", new=mock_watch_impl),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            async for _ in etcd.watch("test-key"):
                pass

        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert all(d <= 30.0 for d in delays)
        # attempt 7: 0.5 * 2^6 = 32.0 → capped at 30.0
        # attempt 8: 0.5 * 2^7 = 64.0 → capped at 30.0
        assert delays[-2] == pytest.approx(30.0)
        assert delays[-1] == pytest.approx(30.0)

    async def test_watch_backoff_resets_on_success(self, etcd: AsyncEtcd) -> None:
        """watch() resets the retry counter to 0 when an event is received after retries."""
        n_initial_failures = 3
        call_count = 0
        err = self._unavail_err()

        async def mock_watch_impl(*args: Any, **kwargs: Any) -> AsyncGenerator[Event, None]:
            nonlocal call_count
            call_count += 1
            if call_count <= n_initial_failures:
                raise err
            if call_count == n_initial_failures + 1:
                # Yield one event (triggers retry_count reset), then simulate disconnect
                yield Event("key", WatchEventType.PUT, "val")
                raise err
            if call_count == n_initial_failures + 2:
                # Second failure after reset — should restart backoff from 0.5 s
                raise err
            empty: list[Event] = []
            for ev in empty:
                yield ev

        with (
            patch.object(etcd, "_watch_impl", new=mock_watch_impl),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            async for _ in etcd.watch("test-key"):
                pass

        delays = [c.args[0] for c in mock_sleep.call_args_list]
        # 3 initial failures: 0.5, 1.0, 2.0
        # After receiving event (retry_count reset to 0), 2 more failures: 0.5, 1.0
        assert delays == pytest.approx([0.5, 1.0, 2.0, 0.5, 1.0])

    async def test_watch_prefix_exponential_backoff(self, etcd: AsyncEtcd) -> None:
        """watch_prefix() uses the same exponential backoff logic as watch()."""
        n_failures = 3
        call_count = 0
        err = self._unavail_err()

        async def mock_watch_impl(*args: Any, **kwargs: Any) -> AsyncGenerator[Event, None]:
            nonlocal call_count
            call_count += 1
            if call_count <= n_failures:
                raise err
            empty: list[Event] = []
            for ev in empty:
                yield ev

        with (
            patch.object(etcd, "_watch_impl", new=mock_watch_impl),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            async for _ in etcd.watch_prefix("test-prefix"):
                pass

        assert mock_sleep.call_count == n_failures
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == pytest.approx([0.5, 1.0, 2.0])

    async def test_watch_log_throttling(
        self, etcd: AsyncEtcd, caplog: pytest.LogCaptureFixture
    ) -> None:
        """watch() emits WARNING on the first failure only; subsequent retries use DEBUG."""
        n_failures = 4
        call_count = 0
        err = self._unavail_err()

        async def mock_watch_impl(*args: Any, **kwargs: Any) -> AsyncGenerator[Event, None]:
            nonlocal call_count
            call_count += 1
            if call_count <= n_failures:
                raise err
            empty: list[Event] = []
            for ev in empty:
                yield ev

        with (
            patch.object(etcd, "_watch_impl", new=mock_watch_impl),
            patch("asyncio.sleep", new_callable=AsyncMock),
            caplog.at_level(logging.DEBUG, logger="ai.backend.common.etcd"),
        ):
            async for _ in etcd.watch("test-key"):
                pass

        warning_recs = [
            r for r in caplog.records if r.levelno == logging.WARNING and "retrying" in str(r.msg)
        ]
        debug_recs = [
            r for r in caplog.records if r.levelno == logging.DEBUG and "still unable" in str(r.msg)
        ]
        assert len(warning_recs) == 1
        assert len(debug_recs) == n_failures - 1
