import enum
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import BaseModel

from ai.backend.appproxy.common.utils import (
    HostPortPair,
    config_key_to_kebab_case,
    ensure_json_serializable,
    mime_match,
)


class SampleModel(BaseModel):
    id: int
    name: str


class SampleEnum(enum.Enum):
    VALUE_1 = "value1"
    VALUE_2 = "value2"


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            {"key": UUID("12345678123456781234567812345678")},
            {"key": "12345678-1234-5678-1234-567812345678"},
        ),
        (
            {"key": UUID(bytes=b"\x12\x34\x56\x78" * 4)},
            {"key": "12345678-1234-5678-1234-567812345678"},
        ),
        (
            {"key": UUID(bytes_le=b"\x12\x34\x56\x78" * 4)},
            {"key": "78563412-3412-7856-1234-567812345678"},
        ),
        (
            {"key": UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))},
            {"key": "12345678-1234-5678-1234-567812345678"},
        ),
        (
            {"key": UUID(int=0x12345678123456781234567812345678)},
            {"key": "12345678-1234-5678-1234-567812345678"},
        ),
        ([UUID("12345678123456781234567812345678")], ["12345678-1234-5678-1234-567812345678"]),
        (UUID("12345678123456781234567812345678"), "12345678-1234-5678-1234-567812345678"),
        (HostPortPair(host="localhost", port=8080), {"host": "localhost", "port": 8080}),
        (Path("/some/path"), "/some/path"),
        (SampleModel(id=1, name="Test"), {"id": 1, "name": "Test"}),
        (SampleEnum.VALUE_1, "value1"),
        (datetime(2024, 7, 16, 5, 45, 45, tzinfo=timezone.utc), 1721108745.0),
        (datetime(2024, 7, 16, 5, 45, 45, tzinfo=timezone(timedelta(hours=9))), 1721076345.0),
    ],
)
def test_ensure_json_serializable(input, expected):
    """
    This test ensures that ensure_json_serializable correctly serializes various
    types of inputs, including dictionaries, lists, UUIDs created in different ways,
    HostPortPair, Path, Pydantic models, enums, and datetime objects.
    """
    assert ensure_json_serializable(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ({"camelCaseKey": "value"}, {"camel-case-key": "value"}),
        (
            {"nestedDict": {"innerCamelCaseKey": "value"}},
            {"nested-dict": {"inner-camel-case-key": "value"}},
        ),
        (["camelCaseListItem"], ["camelCaseListItem"]),
    ],
)
def test_config_key_to_kebab_case(input, expected):
    """
    This test ensures that config_key_to_kebab_case correctly converts keys in dictionaries
    to kebab-case format and handles nested dictionaries and lists.
    """
    assert config_key_to_kebab_case(input) == expected


@pytest.mark.parametrize(
    "base_array, compare, strict, expected",
    [
        ("application/json", "application/json", False, True),
        ("application/*", "application/json", False, True),
        ("application/json,text/plain", "text/plain", False, True),
        ("application/json,text/plain", "text/html", False, False),
        ("application/*", "application/json", True, False),
    ],
)
def test_mime_match(base_array, compare, strict, expected):
    """
    This test ensures that mime_match correctly identifies matching MIME types based on
    the base_array and compare inputs, with and without the strict parameter.
    """
    assert mime_match(base_array, compare, strict) == expected
