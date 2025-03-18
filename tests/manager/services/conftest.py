from typing import Awaitable, Callable, Generic, Optional, Self, TypeVar

import pytest

TInput = TypeVar("TInput")
TResult = TypeVar("TResult")
E = TypeVar("E", bound=Exception)
TException = type[E] | tuple[type[E], ...]


class TestScenario(Generic[TInput, TResult]):
    description: str
    input: TInput
    expected: Optional[TResult]
    expected_exception: Optional[TException]

    def __init__(
        self,
        description: str,
        input: TInput,
        expected: Optional[TResult],
        expected_exception: Optional[TException],
    ):
        self.description = description
        self.input = input
        self.expected = expected
        self.expected_exception = expected_exception

    @classmethod
    def success(cls, description: str, input: TInput, expected: TResult) -> Self:
        return cls(description, input, expected, None)

    @classmethod
    def failure(cls, description: str, input: TInput, expected_exception: TException) -> Self:
        return cls(description, input, None, expected_exception)

    async def test(self, fn: Callable[[TInput], Awaitable[Optional[TResult]]]) -> None:
        # TODO: 예외를 안에서 잡아 처리해버리고 있어서 여기서 안 잡힘...
        # 여기서 예외 처리를 빼든 미들웨어에서 reraise 해야.
        if self.expected_exception is not None:
            with pytest.raises(self.expected_exception):
                result = await fn(self.input)
        else:
            result = await fn(self.input)
            assert result == self.expected

    async def test_bgtask(self, fn: Callable[[TInput], Awaitable[TResult]]) -> None:
        # TODO: Write this for testing background tasks (fire and forget tasks)
        pass
