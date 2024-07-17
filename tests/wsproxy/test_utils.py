import base64
import enum
import hashlib
import hmac
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import BaseModel

from ai.backend.common.types import HostPortPair
from ai.backend.wsproxy.utils import (
    calculate_permit_hash,
    config_key_to_kebab_case,
    ensure_json_serializable,
    is_permit_valid,
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
        (HostPortPair("localhost", 8080), {"host": "localhost", "port": 8080}),
        (Path("/some/path"), "/some/path"),
        (SampleModel(id=1, name="Test"), {"id": 1, "name": "Test"}),
        (SampleEnum.VALUE_1, "value1"),
        (datetime(2024, 7, 16, 5, 45, 45), 1721076345.0),
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


def test_calculate_permit_hash():
    """
    This test ensures that calculate_permit_hash returns the correct hash value for a given
    hash key and user ID.
    """
    hash_key = "secret_key"
    user_id = UUID("12345678123456781234567812345678")
    expected_hash = base64.b64encode(
        hmac.new(hash_key.encode(), str(user_id).encode("utf-8"), hashlib.sha256)
        .hexdigest()
        .encode()
    ).decode()
    assert calculate_permit_hash(hash_key, user_id) == expected_hash


def test_is_permit_valid():
    """
    This test ensures that is_permit_valid correctly validates a permit hash against the expected
    hash value for a given hash key and user ID.
    """
    hash_key = "secret_key"
    user_id = UUID("12345678123456781234567812345678")
    valid_hash = calculate_permit_hash(hash_key, user_id)
    assert is_permit_valid(hash_key, user_id, valid_hash)
    assert not is_permit_valid(hash_key, user_id, "invalid_hash")
