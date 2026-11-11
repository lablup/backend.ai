from __future__ import annotations

import enum
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from pydantic import BaseModel

from ai.backend.appproxy.common.config import HostPortPair, PermitHashConfig
from ai.backend.appproxy.common.utils import (
    calculate_permit_hash,
    config_key_to_kebab_case,
    ensure_json_serializable,
    is_permit_valid,
    mime_match,
    strip_permit_cookie,
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
        (datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC), 1721108745.0),
        (datetime(2024, 7, 16, 5, 45, 45, tzinfo=timezone(timedelta(hours=9))), 1721076345.0),
    ],
)
def test_ensure_json_serializable(input: Any, expected: Any) -> None:
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
def test_config_key_to_kebab_case(input: Any, expected: Any) -> None:
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
def test_mime_match(base_array: str, compare: str, strict: bool, expected: bool) -> None:
    """
    This test ensures that mime_match correctly identifies matching MIME types based on
    the base_array and compare inputs, with and without the strict parameter.
    """
    assert mime_match(base_array, compare, strict) == expected


_PERMIT_USER_ID = UUID("6a1e4c2c-9f0d-4b8e-a0b6-8a7d1f2e3c4b")


@pytest.fixture
def permit_hash_config() -> PermitHashConfig:
    return PermitHashConfig(secret=b"permit-secret")


def test_is_permit_valid_accepts_matching_permit(permit_hash_config: PermitHashConfig) -> None:
    permit = calculate_permit_hash(permit_hash_config, _PERMIT_USER_ID)
    assert is_permit_valid(permit_hash_config, _PERMIT_USER_ID, permit)


@pytest.mark.parametrize(
    "permit",
    [
        "",
        "not-a-permit",
        "\u00e9",
    ],
)
def test_is_permit_valid_rejects_wrong_permit(
    permit_hash_config: PermitHashConfig, permit: str
) -> None:
    assert not is_permit_valid(permit_hash_config, _PERMIT_USER_ID, permit)


def test_is_permit_valid_rejects_other_users_permit(
    permit_hash_config: PermitHashConfig,
) -> None:
    other_permit = calculate_permit_hash(
        permit_hash_config, UUID("0b5f1d7e-3c2a-4e9b-8d6f-1a2b3c4d5e6f")
    )
    assert not is_permit_valid(permit_hash_config, _PERMIT_USER_ID, other_permit)


@pytest.mark.parametrize(
    "cookie_header, expected",
    [
        ("appproxy_permit=abc", None),
        ("appproxy_permit=abc; session=xyz", "session=xyz"),
        ("session=xyz; appproxy_permit=abc; _xsrf=123", "session=xyz; _xsrf=123"),
        ("session=xyz;appproxy_permit=abc", "session=xyz"),
        ("session=xyz; _xsrf=123", "session=xyz; _xsrf=123"),
        ("appproxy_permit_other=abc; session=xyz", "appproxy_permit_other=abc; session=xyz"),
        ("session=appproxy_permit", "session=appproxy_permit"),
        ("", None),
    ],
)
def test_strip_permit_cookie(cookie_header: str, expected: str | None) -> None:
    assert strip_permit_cookie(cookie_header) == expected
