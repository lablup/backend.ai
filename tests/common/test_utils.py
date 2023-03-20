import asyncio
import sys
from collections import OrderedDict
from datetime import timedelta
from pathlib import Path
from random import choice, randint
from string import ascii_uppercase
from tempfile import NamedTemporaryFile
from unittest import mock

import aiohttp
import pytest

from ai.backend.common.asyncio import AsyncBarrier, run_through
from ai.backend.common.enum_extension import StringSetFlag
from ai.backend.common.files import AsyncFileWriter
from ai.backend.common.networking import curl
from ai.backend.common.utils import (
    dict2kvlist,
    generate_uuid,
    get_random_seq,
    nmget,
    odict,
    readable_size_to_bytes,
    str_to_timedelta,
)
from ai.backend.testutils.mock import AsyncContextManagerMock, mock_awaitable, mock_corofunc


def test_odict() -> None:
    assert odict(("a", 1), ("b", 2)) == OrderedDict([("a", 1), ("b", 2)])


def test_dict2kvlist() -> None:
    ret = list(dict2kvlist({"a": 1, "b": 2}))
    assert set(ret) == {"a", 1, "b", 2}


def test_generate_uuid() -> None:
    u = generate_uuid()
    assert len(u) == 22
    assert isinstance(u, str)


def test_random_seq() -> None:
    assert [*get_random_seq(10, 11, 1)] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert [*get_random_seq(10, 6, 2)] == [0, 2, 4, 6, 8, 10]
    with pytest.raises(AssertionError):
        [*get_random_seq(10, 12, 1)]
    with pytest.raises(AssertionError):
        [*get_random_seq(10, 7, 2)]
    for _ in range(30):
        result = [*get_random_seq(10, 9, 1)]
        assert result[0] >= 0
        assert result[-1] <= 10
        last_x = result[0]
        for x in result[1:]:
            assert x > last_x + 1


def test_nmget() -> None:
    o = {"a": {"b": 1}, "x": None}
    assert nmget(o, "a", 0) == {"b": 1}
    assert nmget(o, "a.b", 0) == 1
    assert nmget(o, "a/b", 0, "/") == 1
    assert nmget(o, "a.c", 0) == 0
    assert nmget(o, "a.c", 100) == 100
    assert nmget(o, "x", 0) == 0
    assert nmget(o, "x", 0, null_as_default=False) is None


def test_readable_size_to_bytes() -> None:
    assert readable_size_to_bytes(2) == 2
    assert readable_size_to_bytes("2") == 2
    assert readable_size_to_bytes("2K") == 2 * (2**10)
    assert readable_size_to_bytes("2k") == 2 * (2**10)
    assert readable_size_to_bytes("2M") == 2 * (2**20)
    assert readable_size_to_bytes("2m") == 2 * (2**20)
    assert readable_size_to_bytes("2G") == 2 * (2**30)
    assert readable_size_to_bytes("2g") == 2 * (2**30)
    assert readable_size_to_bytes("2T") == 2 * (2**40)
    assert readable_size_to_bytes("2t") == 2 * (2**40)
    assert readable_size_to_bytes("2P") == 2 * (2**50)
    assert readable_size_to_bytes("2p") == 2 * (2**50)
    assert readable_size_to_bytes("2E") == 2 * (2**60)
    assert readable_size_to_bytes("2e") == 2 * (2**60)
    assert readable_size_to_bytes("2Z") == 2 * (2**70)
    assert readable_size_to_bytes("2z") == 2 * (2**70)
    assert readable_size_to_bytes("2Y") == 2 * (2**80)
    assert readable_size_to_bytes("2y") == 2 * (2**80)
    with pytest.raises(ValueError):
        readable_size_to_bytes("3A")
    with pytest.raises(ValueError):
        readable_size_to_bytes("TT")


def test_str_to_timedelta() -> None:
    assert str_to_timedelta("1d2h3m4s") == timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert str_to_timedelta("1d2h3m") == timedelta(days=1, hours=2, minutes=3)
    assert str_to_timedelta("1d2h") == timedelta(days=1, hours=2)
    assert str_to_timedelta("1d") == timedelta(days=1)
    assert str_to_timedelta("2h3m4s") == timedelta(hours=2, minutes=3, seconds=4)
    assert str_to_timedelta("2h3m") == timedelta(hours=2, minutes=3)
    assert str_to_timedelta("2h") == timedelta(hours=2)
    assert str_to_timedelta("3m4s") == timedelta(minutes=3, seconds=4)
    assert str_to_timedelta("3m") == timedelta(minutes=3)
    assert str_to_timedelta("4s") == timedelta(seconds=4)
    assert str_to_timedelta("4") == timedelta(seconds=4)

    assert str_to_timedelta("+1d2h3m4s") == timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert str_to_timedelta("-1d2h3m4s") == timedelta(days=-1, hours=-2, minutes=-3, seconds=-4)
    assert str_to_timedelta("1day2hr3min4sec") == timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert str_to_timedelta("1day2hour3minute4second") == timedelta(
        days=1, hours=2, minutes=3, seconds=4
    )
    assert str_to_timedelta("1day 2hour 3minute 4second") == timedelta(
        days=1, hours=2, minutes=3, seconds=4
    )
    assert str_to_timedelta("1days 2hours 3minutes 4seconds") == timedelta(
        days=1, hours=2, minutes=3, seconds=4
    )
    assert str_to_timedelta("0.1d0.2h0.3m0.4s") == timedelta(
        days=0.1, hours=0.2, minutes=0.3, seconds=0.4
    )
    assert str_to_timedelta("1d 2h 3m 4s") == timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert str_to_timedelta("-1d 2h 3m 4s") == timedelta(days=-1, hours=-2, minutes=-3, seconds=-4)
    assert str_to_timedelta("- 1d 2h 3m 4s") == timedelta(days=-1, hours=-2, minutes=-3, seconds=-4)

    with pytest.raises(ValueError):
        assert str_to_timedelta("1da1hr")
    with pytest.raises(ValueError):
        assert str_to_timedelta("--1d2h3m4s")
    with pytest.raises(ValueError):
        assert str_to_timedelta("+")
    with pytest.raises(ValueError):
        assert str_to_timedelta("")


@pytest.mark.asyncio
async def test_curl_returns_stripped_body(mocker) -> None:
    mock_get = mocker.patch.object(aiohttp.ClientSession, "get")
    mock_resp = {"status": 200, "text": mock_corofunc(b"success  ")}
    mock_get.return_value = AsyncContextManagerMock(**mock_resp)

    resp = await curl("/test/url", "")

    body = await mock_resp["text"]()
    assert resp == body.strip()


@pytest.mark.asyncio
async def test_curl_returns_default_value_if_not_success(mocker) -> None:
    mock_get = mocker.patch.object(aiohttp.ClientSession, "get")
    mock_resp = {"status": 400, "text": mock_corofunc(b"bad request")}
    mock_get.return_value = AsyncContextManagerMock(**mock_resp)

    # Value.
    resp = await curl("/test/url", default_value="default")
    assert resp == "default"

    # Callable.
    resp = await curl("/test/url", default_value=lambda: "default")
    assert resp == "default"


def test_string_set_flag() -> None:
    class MyFlags(StringSetFlag):
        A = "a"
        B = "b"

    assert MyFlags.A in {"a", "c"}
    assert MyFlags.B not in {"a", "c"}

    assert MyFlags.A in {MyFlags.A, MyFlags.B}
    assert MyFlags.B in {MyFlags.A, MyFlags.B}

    assert MyFlags.A == MyFlags.A
    assert MyFlags.A != MyFlags.B
    assert MyFlags.A == "a"
    assert MyFlags.A != "b"
    assert "a" == MyFlags.A
    assert "b" != MyFlags.A

    assert {"a", "b"} == MyFlags.A | MyFlags.B
    assert {"a", "b"} == MyFlags.A | "b"
    assert {"a", "b"} == "a" | MyFlags.B
    assert {"a", "b", "c"} == {"b", "c"} | MyFlags.A
    assert {"a", "b", "c"} == MyFlags.A | {"b", "c"}

    assert {"b", "c"} == {"a", "b", "c"} ^ MyFlags.A
    assert {"a", "b", "c"} == {"b", "c"} ^ MyFlags.A
    assert set() == MyFlags.A ^ "a"
    assert {"b"} == MyFlags.A ^ {"a", "b"}
    assert {"a", "b", "c"} == MyFlags.A ^ {"b", "c"}
    with pytest.raises(TypeError):
        123 & MyFlags.A  # type: ignore[operator]

    assert {"a", "c"} & MyFlags.A
    assert not {"a", "c"} & MyFlags.B
    assert "a" & MyFlags.A
    assert not "a" & MyFlags.B
    assert MyFlags.A & "a"
    assert not MyFlags.A & "b"
    assert MyFlags.A & {"a", "b"}
    assert not MyFlags.A & {"b", "c"}


class TestAsyncBarrier:
    def test_async_barrier_initialization(self) -> None:
        barrier = AsyncBarrier(num_parties=5)

        assert barrier.num_parties == 5
        assert barrier.cond is not None  # default condition

    @pytest.mark.asyncio
    async def test_wait_notify_all_if_cound_eq_num_parties(self, mocker) -> None:
        mock_cond = mocker.patch.object(asyncio, "Condition")
        mock_resp = {
            "notify_all": mock.Mock(),
            "wait": await mock_awaitable(),
        }
        mock_cond.return_value = AsyncContextManagerMock(**mock_resp)

        barrier = AsyncBarrier(num_parties=1)
        assert barrier.count == 0

        await barrier.wait()

        assert barrier.count == 1
        # The methods are added at runtime.
        mock_cond.return_value.notify_all.assert_called_once_with()  # type: ignore
        mock_cond.return_value.wait.assert_not_called()  # type: ignore

    def test_async_barrier_reset(self):
        barrier = AsyncBarrier(num_parties=5)
        barrier.count = 5

        assert barrier.count == 5
        barrier.reset()
        assert barrier.count == 0


@pytest.mark.asyncio
async def test_run_through() -> None:
    i = 0

    async def do():
        nonlocal i
        i += 1
        raise ZeroDivisionError

    def do_sync():
        nonlocal i
        i += 1
        raise ZeroDivisionError

    await run_through(
        do(),
        do(),
        do(),
        ignored_exceptions=(ZeroDivisionError,),
    )
    assert i == 3

    with pytest.raises(ZeroDivisionError):
        await run_through(
            do(),
            do(),
            do(),
            ignored_exceptions=(KeyError,),
        )
    # only the addition is executed.
    assert i == 4

    await run_through(
        do,  # coroutine-function
        do_sync,  # function
        lambda: do_sync(),  # function wrapped with lambda
        do(),  # coroutine
        ignored_exceptions=(ZeroDivisionError,),
    )
    assert i == 8


@pytest.mark.asyncio
async def test_async_file_writer_str() -> None:
    # 1. Get temporary filename
    with NamedTemporaryFile() as temp_file:
        file_name = temp_file.name

    # 2. Generate random string
    init_str = "".join(choice(ascii_uppercase) for i in range(100))

    # 3. Write chuncked decoded string into file
    async with AsyncFileWriter(
        target_filename=file_name,
        access_mode="w",
        encode=lambda v: v.upper().encode(),
        max_chunks=1,
    ) as file_writer:
        for i in range(0, 100, 20):
            await file_writer.write(init_str[i : i + 20])

    # 4. Read string from the file and close it
    with open(file_name, "r") as f:
        final_str = f.read()
    Path(file_name).unlink()

    # 5. Check initial and final strings
    assert init_str.upper() == final_str


@pytest.mark.asyncio
async def test_async_file_writer_bytes() -> None:
    # 1. Get temporary filename
    with NamedTemporaryFile() as temp_file:
        file_name = temp_file.name

    # 2. Generate random binary data
    init_data = b"".join(randint(0, 255).to_bytes(1, sys.byteorder) for i in range(100))

    def dummy_encode(v: str) -> bytes:
        assert False, "should not be called"

    # 3. Write chuncked decoded string into file
    async with AsyncFileWriter(
        target_filename=file_name,
        access_mode="wb",
        encode=dummy_encode,
        max_chunks=1,
    ) as file_writer:
        for i in range(0, 100, 20):
            await file_writer.write(init_data[i : i + 20])

    # 4. Read string from the file and close it
    with open(file_name, "rb") as f:
        final_data = f.read()
    Path(file_name).unlink()

    # 5. Check initial and final data
    assert init_data == final_data
