from typing import Callable, Generic, Optional, TypeVar

import pytest

TInput = TypeVar("TInput")
TResult = TypeVar("TResult")
E = TypeVar("E", bound=BaseException)
TException = type[E] | tuple[type[E], ...]


class TestScenario(Generic[TInput, TResult]):
    description: str
    input: TInput
    expected: Optional[TResult]
    expected_exception: TException

    def __init__(
        self,
        description: str,
        input: TInput,
        expected: Optional[TResult],
        expected_exception: TException,
    ):
        self.description = description
        self.input = input
        self.expected = expected
        self.expected_exception = expected_exception

    @classmethod
    def success(cls, description: str, input: TInput, expected: TResult):
        return cls(description, input, expected, None)

    @classmethod
    def failure(cls, description: str, input: TInput, expected_exception: TException):
        return cls(description, input, None, expected_exception)

    def test(self, fn: Callable[[TInput], TResult]):
        if self.expected_exception is not None:
            with pytest.raises(self.expected_exception):
                result = fn(self.input)
        else:
            result = fn(self.input)
            assert result == self.expected
