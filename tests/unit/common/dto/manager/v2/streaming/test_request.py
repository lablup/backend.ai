"""Tests for ai.backend.common.dto.manager.v2.streaming.request module."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from ai.backend.common.dto.manager.v2.streaming.request import (
    ExecuteInput,
    PtyClientInput,
    PtyPingInput,
    PtyResizeInput,
    PtyRestartInput,
    PtyStdinInput,
    StreamProxyInput,
)
from ai.backend.common.dto.manager.v2.streaming.types import ExecuteMode, PtyInputMessageType


class TestPtyStdinInput:
    """Tests for PtyStdinInput model."""

    def test_valid_creation(self) -> None:
        req = PtyStdinInput(type=PtyInputMessageType.STDIN, chars="hello")
        assert req.type == PtyInputMessageType.STDIN
        assert req.chars == "hello"

    def test_type_literal_value(self) -> None:
        req = PtyStdinInput(type=PtyInputMessageType.STDIN, chars="a")
        assert req.type.value == "stdin"

    def test_from_dict(self) -> None:
        req = PtyStdinInput.model_validate({"type": "stdin", "chars": "test"})
        assert req.type == PtyInputMessageType.STDIN
        assert req.chars == "test"

    def test_round_trip_serialization(self) -> None:
        req = PtyStdinInput(type=PtyInputMessageType.STDIN, chars="hello world")
        json_data = req.model_dump_json()
        restored = PtyStdinInput.model_validate_json(json_data)
        assert restored.type == req.type
        assert restored.chars == req.chars


class TestPtyResizeInput:
    """Tests for PtyResizeInput model."""

    def test_valid_creation(self) -> None:
        req = PtyResizeInput(type=PtyInputMessageType.RESIZE, rows=24, cols=80)
        assert req.type == PtyInputMessageType.RESIZE
        assert req.rows == 24
        assert req.cols == 80

    def test_from_dict(self) -> None:
        req = PtyResizeInput.model_validate({"type": "resize", "rows": 50, "cols": 120})
        assert req.rows == 50
        assert req.cols == 120

    def test_round_trip_serialization(self) -> None:
        req = PtyResizeInput(type=PtyInputMessageType.RESIZE, rows=24, cols=80)
        json_data = req.model_dump_json()
        restored = PtyResizeInput.model_validate_json(json_data)
        assert restored.rows == req.rows
        assert restored.cols == req.cols


class TestPtyPingInput:
    """Tests for PtyPingInput model."""

    def test_valid_creation(self) -> None:
        req = PtyPingInput(type=PtyInputMessageType.PING)
        assert req.type == PtyInputMessageType.PING

    def test_from_dict(self) -> None:
        req = PtyPingInput.model_validate({"type": "ping"})
        assert req.type == PtyInputMessageType.PING

    def test_round_trip_serialization(self) -> None:
        req = PtyPingInput(type=PtyInputMessageType.PING)
        json_data = req.model_dump_json()
        restored = PtyPingInput.model_validate_json(json_data)
        assert restored.type == req.type


class TestPtyRestartInput:
    """Tests for PtyRestartInput model."""

    def test_valid_creation(self) -> None:
        req = PtyRestartInput(type=PtyInputMessageType.RESTART)
        assert req.type == PtyInputMessageType.RESTART

    def test_from_dict(self) -> None:
        req = PtyRestartInput.model_validate({"type": "restart"})
        assert req.type == PtyInputMessageType.RESTART

    def test_round_trip_serialization(self) -> None:
        req = PtyRestartInput(type=PtyInputMessageType.RESTART)
        json_data = req.model_dump_json()
        restored = PtyRestartInput.model_validate_json(json_data)
        assert restored.type == req.type


class TestPtyClientInputDiscriminatedUnion:
    """Tests for PtyClientInput discriminated union parsing."""

    def test_parses_stdin_message(self) -> None:
        adapter: TypeAdapter[PtyClientInput] = TypeAdapter(PtyClientInput)
        result = adapter.validate_python({"type": "stdin", "chars": "a"})
        assert isinstance(result, PtyStdinInput)
        assert result.chars == "a"

    def test_parses_resize_message(self) -> None:
        adapter: TypeAdapter[PtyClientInput] = TypeAdapter(PtyClientInput)
        result = adapter.validate_python({"type": "resize", "rows": 24, "cols": 80})
        assert isinstance(result, PtyResizeInput)
        assert result.rows == 24
        assert result.cols == 80

    def test_parses_ping_message(self) -> None:
        adapter: TypeAdapter[PtyClientInput] = TypeAdapter(PtyClientInput)
        result = adapter.validate_python({"type": "ping"})
        assert isinstance(result, PtyPingInput)

    def test_parses_restart_message(self) -> None:
        adapter: TypeAdapter[PtyClientInput] = TypeAdapter(PtyClientInput)
        result = adapter.validate_python({"type": "restart"})
        assert isinstance(result, PtyRestartInput)

    def test_invalid_type_raises_error(self) -> None:
        adapter: TypeAdapter[PtyClientInput] = TypeAdapter(PtyClientInput)
        with pytest.raises(ValidationError):
            adapter.validate_python({"type": "unknown"})

    def test_stdin_missing_chars_raises_error(self) -> None:
        adapter: TypeAdapter[PtyClientInput] = TypeAdapter(PtyClientInput)
        with pytest.raises(ValidationError):
            adapter.validate_python({"type": "stdin"})


class TestExecuteInput:
    """Tests for ExecuteInput model."""

    def test_valid_creation_with_mode(self) -> None:
        req = ExecuteInput(mode=ExecuteMode.QUERY)
        assert req.mode == ExecuteMode.QUERY
        assert req.code == ""
        assert req.options == {}

    def test_valid_creation_with_all_fields(self) -> None:
        req = ExecuteInput(
            mode=ExecuteMode.BATCH,
            code="print('hello')",
            options={"timeout": 30},
        )
        assert req.mode == ExecuteMode.BATCH
        assert req.code == "print('hello')"
        assert req.options == {"timeout": 30}

    def test_default_code_is_empty_string(self) -> None:
        req = ExecuteInput(mode=ExecuteMode.QUERY)
        assert req.code == ""

    def test_default_options_is_empty_dict(self) -> None:
        req = ExecuteInput(mode=ExecuteMode.QUERY)
        assert req.options == {}

    def test_from_string_mode(self) -> None:
        req = ExecuteInput.model_validate({"mode": "query"})
        assert req.mode == ExecuteMode.QUERY

    def test_round_trip_serialization(self) -> None:
        req = ExecuteInput(
            mode=ExecuteMode.BATCH,
            code="x = 1",
            options={"lang": "python3"},
        )
        json_data = req.model_dump_json()
        restored = ExecuteInput.model_validate_json(json_data)
        assert restored.mode == req.mode
        assert restored.code == req.code
        assert restored.options == req.options


class TestStreamProxyInput:
    """Tests for StreamProxyInput model validation."""

    def test_valid_creation_with_app_only(self) -> None:
        req = StreamProxyInput(app="jupyter")
        assert req.app == "jupyter"
        assert req.port is None
        assert req.envs is None
        assert req.arguments is None

    def test_valid_port_within_range(self) -> None:
        req = StreamProxyInput(app="jupyter", port=8080)
        assert req.port == 8080

    def test_valid_port_at_lower_bound(self) -> None:
        req = StreamProxyInput(app="app", port=1024)
        assert req.port == 1024

    def test_valid_port_at_upper_bound(self) -> None:
        req = StreamProxyInput(app="app", port=65535)
        assert req.port == 65535

    def test_port_below_1024_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            StreamProxyInput(app="jupyter", port=999)

    def test_port_above_65535_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            StreamProxyInput(app="jupyter", port=65536)

    def test_port_zero_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            StreamProxyInput(app="jupyter", port=0)

    def test_creation_with_envs_and_arguments(self) -> None:
        req = StreamProxyInput(
            app="jupyter",
            port=8888,
            envs='{"JUPYTER_TOKEN": "abc123"}',
            arguments='{"--NotebookApp.token": ""}',
        )
        assert req.envs == '{"JUPYTER_TOKEN": "abc123"}'
        assert req.arguments == '{"--NotebookApp.token": ""}'

    def test_round_trip_serialization(self) -> None:
        req = StreamProxyInput(
            app="jupyter",
            port=8888,
            envs='{"TOKEN": "xyz"}',
            arguments="{}",
        )
        json_data = req.model_dump_json()
        restored = StreamProxyInput.model_validate_json(json_data)
        assert restored.app == req.app
        assert restored.port == req.port
        assert restored.envs == req.envs
        assert restored.arguments == req.arguments
