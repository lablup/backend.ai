"""Tests for ai.backend.common.dto.manager.v2.streaming.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.streaming.response import (
    ExecuteResultNode,
    GetStreamAppsPayload,
    PtyOutputNode,
)
from ai.backend.common.dto.manager.v2.streaming.types import PtyOutputMessageType, StreamAppInfoNode


class TestPtyOutputNode:
    """Tests for PtyOutputNode model."""

    def test_creation_with_required_fields(self) -> None:
        node = PtyOutputNode(type=PtyOutputMessageType.OUT, data="dGVzdA==")
        assert node.type == PtyOutputMessageType.OUT
        assert node.data == "dGVzdA=="

    def test_type_literal_value(self) -> None:
        node = PtyOutputNode(type=PtyOutputMessageType.OUT, data="abc")
        assert node.type.value == "out"

    def test_from_dict(self) -> None:
        node = PtyOutputNode.model_validate({"type": "out", "data": "dGVzdA=="})
        assert node.type == PtyOutputMessageType.OUT
        assert node.data == "dGVzdA=="

    def test_round_trip_serialization(self) -> None:
        node = PtyOutputNode(type=PtyOutputMessageType.OUT, data="base64data")
        json_str = node.model_dump_json()
        restored = PtyOutputNode.model_validate_json(json_str)
        assert restored.type == node.type
        assert restored.data == node.data

    def test_model_dump_json_has_expected_keys(self) -> None:
        node = PtyOutputNode(type=PtyOutputMessageType.OUT, data="abc")
        data = json.loads(node.model_dump_json())
        assert "type" in data
        assert "data" in data
        assert data["type"] == "out"


class TestExecuteResultNode:
    """Tests for ExecuteResultNode model."""

    def test_creation_with_status_only(self) -> None:
        node = ExecuteResultNode(status="finished")
        assert node.status == "finished"
        assert node.console is None
        assert node.exit_code is None
        assert node.options is None
        assert node.files is None
        assert node.msg is None

    def test_creation_with_all_optional_fields(self) -> None:
        node = ExecuteResultNode(
            status="finished",
            console=[["stdout", "Hello"]],
            exit_code=0,
            options={"key": "value"},
            files={"output.txt": "/path/to/output.txt"},
            msg="Execution successful",
        )
        assert node.status == "finished"
        assert node.console == [["stdout", "Hello"]]
        assert node.exit_code == 0
        assert node.options == {"key": "value"}
        assert node.files == {"output.txt": "/path/to/output.txt"}
        assert node.msg == "Execution successful"

    def test_exit_code_can_be_nonzero(self) -> None:
        node = ExecuteResultNode(status="error", exit_code=1)
        assert node.exit_code == 1

    def test_round_trip_serialization_with_all_fields(self) -> None:
        node = ExecuteResultNode(
            status="finished",
            console=[["stdout", "output"]],
            exit_code=0,
            options={"timeout": 30},
            files={"result.txt": "/tmp/result.txt"},
            msg="Done",
        )
        json_str = node.model_dump_json()
        restored = ExecuteResultNode.model_validate_json(json_str)
        assert restored.status == node.status
        assert restored.console == node.console
        assert restored.exit_code == node.exit_code
        assert restored.options == node.options
        assert restored.files == node.files
        assert restored.msg == node.msg

    def test_round_trip_preserves_none_optionals(self) -> None:
        node = ExecuteResultNode(status="waiting-input")
        json_str = node.model_dump_json()
        restored = ExecuteResultNode.model_validate_json(json_str)
        assert restored.console is None
        assert restored.exit_code is None
        assert restored.options is None
        assert restored.files is None
        assert restored.msg is None

    def test_model_dump_json_has_snake_case_keys(self) -> None:
        node = ExecuteResultNode(status="finished", exit_code=0)
        data = json.loads(node.model_dump_json())
        assert "exit_code" in data
        assert "exitCode" not in data


class TestGetStreamAppsPayload:
    """Tests for GetStreamAppsPayload model."""

    def test_creation_with_empty_apps(self) -> None:
        payload = GetStreamAppsPayload(apps=[])
        assert payload.apps == []

    def test_creation_with_single_app(self) -> None:
        app = StreamAppInfoNode(name="jupyter", protocol="http", ports=[8888])
        payload = GetStreamAppsPayload(apps=[app])
        assert len(payload.apps) == 1
        assert payload.apps[0].name == "jupyter"

    def test_creation_with_multiple_apps(self) -> None:
        apps = [
            StreamAppInfoNode(name="jupyter", protocol="http", ports=[8888]),
            StreamAppInfoNode(name="tensorboard", protocol="http", ports=[6006]),
            StreamAppInfoNode(name="vnc", protocol="vnc", ports=[5900]),
        ]
        payload = GetStreamAppsPayload(apps=apps)
        assert len(payload.apps) == 3
        assert payload.apps[1].name == "tensorboard"

    def test_apps_is_list_of_stream_app_info_node(self) -> None:
        app = StreamAppInfoNode(name="app", protocol="tcp", ports=[9000])
        payload = GetStreamAppsPayload(apps=[app])
        assert isinstance(payload.apps[0], StreamAppInfoNode)

    def test_round_trip_serialization_with_apps(self) -> None:
        apps = [
            StreamAppInfoNode(
                name="jupyter",
                protocol="http",
                ports=[8888],
                url_template="/proxy/{port}",
            ),
        ]
        payload = GetStreamAppsPayload(apps=apps)
        json_str = payload.model_dump_json()
        restored = GetStreamAppsPayload.model_validate_json(json_str)
        assert len(restored.apps) == 1
        assert restored.apps[0].name == "jupyter"
        assert restored.apps[0].ports == [8888]
        assert restored.apps[0].url_template == "/proxy/{port}"

    def test_round_trip_empty_apps(self) -> None:
        payload = GetStreamAppsPayload(apps=[])
        json_str = payload.model_dump_json()
        restored = GetStreamAppsPayload.model_validate_json(json_str)
        assert restored.apps == []
