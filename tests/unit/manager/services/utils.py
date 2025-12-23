from typing import Awaitable, Callable, Generic, Optional, Self, TypeVar

import pytest

TInput = TypeVar("TInput")
TResult = TypeVar("TResult")
E = TypeVar("E", bound=BaseException)
TException = type[E] | tuple[type[E], ...]


class ScenarioBase(Generic[TInput, TResult]):
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
        if self.expected_exception is not None:
            with pytest.raises(self.expected_exception):
                result = await fn(self.input)
                print(f"error result: {result}")
        else:
            result = await fn(self.input)
            assert result == self.expected
