"""Tests for ai.backend.common.dto.manager.v2.error_log.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.error_log.types import (
    ErrorLogContextInfo,
    ErrorLogRequestInfo,
)


class TestErrorLogContextInfo:
    """Tests for ErrorLogContextInfo response sub-model."""

    def test_creation_with_all_fields(self) -> None:
        info = ErrorLogContextInfo(
            context_lang="python",
            context_env={"version": "3.11", "os": "linux"},
        )
        assert info.context_lang == "python"
        assert info.context_env == {"version": "3.11", "os": "linux"}

    def test_creation_with_empty_env(self) -> None:
        info = ErrorLogContextInfo(
            context_lang="javascript",
            context_env={},
        )
        assert info.context_lang == "javascript"
        assert info.context_env == {}

    def test_creation_from_dict(self) -> None:
        info = ErrorLogContextInfo.model_validate({
            "context_lang": "go",
            "context_env": {"goversion": "1.21"},
        })
        assert info.context_lang == "go"
        assert info.context_env["goversion"] == "1.21"

    def test_model_dump_json(self) -> None:
        info = ErrorLogContextInfo(
            context_lang="python",
            context_env={"key": "value"},
        )
        parsed = json.loads(info.model_dump_json())
        assert parsed["context_lang"] == "python"
        assert parsed["context_env"] == {"key": "value"}

    def test_round_trip_serialization(self) -> None:
        info = ErrorLogContextInfo(
            context_lang="rust",
            context_env={"edition": "2021", "target": "x86_64-linux"},
        )
        json_str = info.model_dump_json()
        restored = ErrorLogContextInfo.model_validate_json(json_str)
        assert restored.context_lang == info.context_lang
        assert restored.context_env == info.context_env

    def test_context_env_can_have_nested_values(self) -> None:
        info = ErrorLogContextInfo(
            context_lang="python",
            context_env={"deps": {"pydantic": "2.0", "fastapi": "0.100"}},
        )
        assert info.context_env["deps"]["pydantic"] == "2.0"


class TestErrorLogRequestInfo:
    """Tests for ErrorLogRequestInfo response sub-model."""

    def test_creation_with_all_fields(self) -> None:
        info = ErrorLogRequestInfo(
            request_url="/api/v2/resource",
            request_status=500,
        )
        assert info.request_url == "/api/v2/resource"
        assert info.request_status == 500

    def test_default_request_url_is_none(self) -> None:
        info = ErrorLogRequestInfo()
        assert info.request_url is None

    def test_default_request_status_is_none(self) -> None:
        info = ErrorLogRequestInfo()
        assert info.request_status is None

    def test_creation_with_no_fields(self) -> None:
        info = ErrorLogRequestInfo()
        assert info.request_url is None
        assert info.request_status is None

    def test_creation_from_dict(self) -> None:
        info = ErrorLogRequestInfo.model_validate({
            "request_url": "/api/sessions",
            "request_status": 404,
        })
        assert info.request_url == "/api/sessions"
        assert info.request_status == 404

    def test_explicit_none_fields(self) -> None:
        info = ErrorLogRequestInfo(request_url=None, request_status=None)
        assert info.request_url is None
        assert info.request_status is None

    def test_model_dump_json(self) -> None:
        info = ErrorLogRequestInfo(
            request_url="/api/compute",
            request_status=400,
        )
        parsed = json.loads(info.model_dump_json())
        assert parsed["request_url"] == "/api/compute"
        assert parsed["request_status"] == 400

    def test_round_trip_serialization(self) -> None:
        info = ErrorLogRequestInfo(
            request_url="/api/kernels",
            request_status=503,
        )
        json_str = info.model_dump_json()
        restored = ErrorLogRequestInfo.model_validate_json(json_str)
        assert restored.request_url == info.request_url
        assert restored.request_status == info.request_status

    def test_round_trip_with_none_fields(self) -> None:
        info = ErrorLogRequestInfo()
        json_str = info.model_dump_json()
        restored = ErrorLogRequestInfo.model_validate_json(json_str)
        assert restored.request_url is None
        assert restored.request_status is None
