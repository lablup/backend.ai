"""Tests for ai.backend.common.dto.manager.v2.streaming.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.streaming.types import (
    ExecuteMode,
    ExecuteResultStatus,
    PtyInputMessageType,
    PtyOutputMessageType,
    ServiceProtocol,
    StreamAppInfoNode,
)


class TestPtyInputMessageType:
    """Tests for PtyInputMessageType StrEnum."""

    def test_stdin_value(self) -> None:
        assert PtyInputMessageType.STDIN.value == "stdin"

    def test_resize_value(self) -> None:
        assert PtyInputMessageType.RESIZE.value == "resize"

    def test_ping_value(self) -> None:
        assert PtyInputMessageType.PING.value == "ping"

    def test_restart_value(self) -> None:
        assert PtyInputMessageType.RESTART.value == "restart"

    def test_enum_members_count(self) -> None:
        assert len(list(PtyInputMessageType)) == 4

    def test_all_values_are_strings(self) -> None:
        for member in PtyInputMessageType:
            assert isinstance(member.value, str)

    def test_from_string_stdin(self) -> None:
        assert PtyInputMessageType("stdin") is PtyInputMessageType.STDIN

    def test_from_string_restart(self) -> None:
        assert PtyInputMessageType("restart") is PtyInputMessageType.RESTART


class TestPtyOutputMessageType:
    """Tests for PtyOutputMessageType StrEnum."""

    def test_out_value(self) -> None:
        assert PtyOutputMessageType.OUT.value == "out"

    def test_enum_members_count(self) -> None:
        assert len(list(PtyOutputMessageType)) == 1

    def test_from_string_out(self) -> None:
        assert PtyOutputMessageType("out") is PtyOutputMessageType.OUT


class TestExecuteMode:
    """Tests for ExecuteMode StrEnum."""

    def test_query_value(self) -> None:
        assert ExecuteMode.QUERY.value == "query"

    def test_batch_value(self) -> None:
        assert ExecuteMode.BATCH.value == "batch"

    def test_enum_members_count(self) -> None:
        assert len(list(ExecuteMode)) == 2

    def test_all_values_are_strings(self) -> None:
        for member in ExecuteMode:
            assert isinstance(member.value, str)

    def test_from_string_query(self) -> None:
        assert ExecuteMode("query") is ExecuteMode.QUERY

    def test_from_string_batch(self) -> None:
        assert ExecuteMode("batch") is ExecuteMode.BATCH


class TestExecuteResultStatus:
    """Tests for ExecuteResultStatus StrEnum."""

    def test_waiting_input_value(self) -> None:
        assert ExecuteResultStatus.WAITING_INPUT.value == "waiting-input"

    def test_finished_value(self) -> None:
        assert ExecuteResultStatus.FINISHED.value == "finished"

    def test_error_value(self) -> None:
        assert ExecuteResultStatus.ERROR.value == "error"

    def test_server_restarting_value(self) -> None:
        assert ExecuteResultStatus.SERVER_RESTARTING.value == "server-restarting"

    def test_enum_members_count(self) -> None:
        assert len(list(ExecuteResultStatus)) == 4

    def test_all_values_are_strings(self) -> None:
        for member in ExecuteResultStatus:
            assert isinstance(member.value, str)

    def test_from_string_finished(self) -> None:
        assert ExecuteResultStatus("finished") is ExecuteResultStatus.FINISHED

    def test_from_string_waiting_input(self) -> None:
        assert ExecuteResultStatus("waiting-input") is ExecuteResultStatus.WAITING_INPUT


class TestServiceProtocol:
    """Tests for ServiceProtocol StrEnum."""

    def test_tcp_value(self) -> None:
        assert ServiceProtocol.TCP.value == "tcp"

    def test_http_value(self) -> None:
        assert ServiceProtocol.HTTP.value == "http"

    def test_preopen_value(self) -> None:
        assert ServiceProtocol.PREOPEN.value == "preopen"

    def test_vnc_value(self) -> None:
        assert ServiceProtocol.VNC.value == "vnc"

    def test_rdp_value(self) -> None:
        assert ServiceProtocol.RDP.value == "rdp"

    def test_enum_members_count(self) -> None:
        assert len(list(ServiceProtocol)) == 5

    def test_all_values_are_strings(self) -> None:
        for member in ServiceProtocol:
            assert isinstance(member.value, str)

    def test_from_string_http(self) -> None:
        assert ServiceProtocol("http") is ServiceProtocol.HTTP


class TestStreamAppInfoNode:
    """Tests for StreamAppInfoNode model creation and serialization."""

    def test_creation_with_required_fields(self) -> None:
        node = StreamAppInfoNode(name="jupyter", protocol="http", ports=[8888])
        assert node.name == "jupyter"
        assert node.protocol == "http"
        assert node.ports == [8888]
        assert node.url_template is None
        assert node.allowed_arguments is None
        assert node.allowed_envs is None

    def test_creation_with_all_fields(self) -> None:
        node = StreamAppInfoNode(
            name="jupyter",
            protocol="http",
            ports=[8888, 8889],
            url_template="/notebooks/{path}",
            allowed_arguments={"--port": {"type": "integer"}},
            allowed_envs={"JUPYTER_TOKEN": {"type": "string"}},
        )
        assert node.name == "jupyter"
        assert node.ports == [8888, 8889]
        assert node.url_template == "/notebooks/{path}"
        assert node.allowed_arguments == {"--port": {"type": "integer"}}
        assert node.allowed_envs == {"JUPYTER_TOKEN": {"type": "string"}}

    def test_creation_with_multiple_ports(self) -> None:
        node = StreamAppInfoNode(name="vnc", protocol="vnc", ports=[5900, 5901])
        assert len(node.ports) == 2
        assert 5900 in node.ports

    def test_round_trip_serialization(self) -> None:
        node = StreamAppInfoNode(
            name="app",
            protocol="tcp",
            ports=[9000],
            url_template="/proxy",
        )
        json_str = node.model_dump_json()
        restored = StreamAppInfoNode.model_validate_json(json_str)
        assert restored.name == node.name
        assert restored.protocol == node.protocol
        assert restored.ports == node.ports
        assert restored.url_template == node.url_template

    def test_model_dump_json_has_snake_case_keys(self) -> None:
        node = StreamAppInfoNode(
            name="app",
            protocol="http",
            ports=[8080],
            url_template="/app",
            allowed_arguments={},
            allowed_envs={},
        )
        data = json.loads(node.model_dump_json())
        assert "url_template" in data
        assert "allowed_arguments" in data
        assert "allowed_envs" in data
        assert "urlTemplate" not in data
        assert "allowedArguments" not in data
        assert "allowedEnvs" not in data

    def test_serialization_with_null_optionals(self) -> None:
        node = StreamAppInfoNode(name="app", protocol="http", ports=[8080])
        data = json.loads(node.model_dump_json())
        assert data["url_template"] is None
        assert data["allowed_arguments"] is None
        assert data["allowed_envs"] is None
