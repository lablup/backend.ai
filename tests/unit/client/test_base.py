from __future__ import annotations

import asyncio
from collections.abc import Iterator
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from ai.backend.client.config import API_VERSION
from ai.backend.client.func.base import BaseFunction, api_function
from ai.backend.client.session import AsyncSession, Session


@pytest.fixture(scope="module", autouse=True)
def api_version() -> Iterator[tuple[int, str]]:
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield API_VERSION


class DummyFunction:
    session = None

    @api_function
    @classmethod
    async def get_or_create(cls) -> str:
        await asyncio.sleep(0)
        return "created"

    @api_function
    async def calculate(self) -> str:
        await asyncio.sleep(0)
        return "done"


def test_api_function_metaclass() -> None:
    # Here, we repeat intentionally the same stuffs
    # to check if our metaclass works across multiple
    # re-definition and re-instantiation scenarios.

    with Session() as session:
        Dummy = type(
            "DummyFunction",
            (BaseFunction,),
            {
                **DummyFunction.__dict__,
                "session": session,
            },
        )

        assert Dummy.session is session
        assert Dummy().session is session

        assert Dummy.get_or_create() == "created"
        assert Dummy().calculate() == "done"
        assert Dummy.get_or_create() == "created"
        assert Dummy().calculate() == "done"

    with Session() as session:
        Dummy = type(
            "DummyFunction",
            (BaseFunction,),
            {
                **DummyFunction.__dict__,
                "session": session,
            },
        )

        assert Dummy.session is session
        assert Dummy().session is session

        assert Dummy.get_or_create() == "created"
        assert Dummy().calculate() == "done"
        assert Dummy.get_or_create() == "created"
        assert Dummy().calculate() == "done"


@pytest.mark.asyncio
async def test_api_function_metaclass_async() -> None:
    async with AsyncSession() as session:
        Dummy = type(
            "DummyFunction",
            (BaseFunction,),
            {
                **DummyFunction.__dict__,
                "session": session,
            },
        )

        assert Dummy.session is session
        assert Dummy().session is session

        assert await Dummy.get_or_create() == "created"
        assert await Dummy().calculate() == "done"
        assert await Dummy.get_or_create() == "created"
        assert await Dummy().calculate() == "done"

    async with AsyncSession() as session:
        Dummy = type(
            "DummyFunction",
            (BaseFunction,),
            {
                **DummyFunction.__dict__,
                "session": session,
            },
        )

        assert Dummy.session is session
        assert Dummy().session is session

        assert await Dummy.get_or_create() == "created"
        assert await Dummy().calculate() == "done"
        assert await Dummy.get_or_create() == "created"
        assert await Dummy().calculate() == "done"
