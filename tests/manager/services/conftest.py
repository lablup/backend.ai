from dataclasses import fields, is_dataclass
from typing import Any, Awaitable, Callable, Generic, Optional, Self, TypeVar

import pytest

TInput = TypeVar("TInput")
TResult = TypeVar("TResult")
E = TypeVar("E", bound=BaseException)
TException = type[E] | tuple[type[E], ...]


def format_value_with_type(v: Any) -> str:
    """
    Returns a string with the format: "stringified_value" (TypeName)
    Example: "11111111-1111-1111-1111-111111111111" (str)
    """
    # str()로 변환한 결과를 쌍따옴표로 감싸고, 뒤에 (타입이름)을 붙여준다.
    return f'"{str(v)}" ({type(v).__name__})'


def diff_dataclass_fields(actual: Any, expected: Any, prefix: str = "") -> list[str]:
    """
    Recursively compare two dataclass instances (or other objects).
    Return a list of strings, each describing a differing field
    in the format:
        - field_path: expected="xxx" (Type), actual="yyy" (Type)

    If either of them is not a dataclass at some level, it compares them directly.
    """
    # If either is not a dataclass, just compare directly
    if not (is_dataclass(actual) and is_dataclass(expected)):
        if actual != expected:
            field_label = prefix or "value"
            return [
                f"- {field_label}: "
                f"expected={format_value_with_type(expected)}, "
                f"actual={format_value_with_type(actual)}"
            ]
        else:
            return []

    diffs = []
    # Both are dataclasses, so compare their fields
    for f in fields(actual):
        field_name = f.name
        v_actual = getattr(actual, field_name)
        v_expected = getattr(expected, field_name)
        # Build a path like "image.created_at" if prefix is "image"
        new_prefix = f"{prefix}.{field_name}" if prefix else field_name

        if v_actual != v_expected:
            if is_dataclass(v_actual) and is_dataclass(v_expected):
                # Recurse deeper
                sub_diffs = diff_dataclass_fields(v_actual, v_expected, prefix=new_prefix)
                diffs.extend(sub_diffs)
            else:
                # Record the difference with value + type
                diffs.append(
                    f"- {new_prefix}: "
                    f"expected={format_value_with_type(v_expected)}, "
                    f"actual={format_value_with_type(v_actual)}"
                )
    return diffs


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
        if self.expected_exception is not None:
            with pytest.raises(self.expected_exception):
                result = await fn(self.input)
        else:
            result = await fn(self.input)

            if result != self.expected:
                # Collect detailed differences
                diffs = diff_dataclass_fields(result, self.expected)

                # If we found any differences, raise with a helpful message
                if diffs:
                    diff_msg = "\n".join(diffs)
                    raise AssertionError(
                        "Dataclass mismatch. The following fields differ:\n"
                        f"{diff_msg}\n\n"
                        f"Actual result={result}\n"
                        f"Expected={self.expected}"
                    )
                else:
                    # Fallback (unlikely case) if no explicit diffs found but objects differ
                    raise AssertionError(
                        f"Dataclass mismatch but no field differences found.\n"
                        f"Actual={result}\nExpected={self.expected}"
                    )

            assert result == self.expected
