"""Tests for ai.backend.common.dto.manager.v2.config.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.config.response import (
    BootstrapScriptNode,
    CreateDotfilePayload,
    DeleteDotfilePayload,
    DotfileListPayload,
    DotfileNode,
    UpdateBootstrapScriptPayload,
    UpdateDotfilePayload,
)


class TestDotfileNodeCreation:
    """Tests for DotfileNode model creation."""

    def test_creation_with_all_fields(self) -> None:
        node = DotfileNode(
            path="/home/user/.bashrc",
            permission="755",
            data="export PATH=$PATH:/usr/local/bin",
        )
        assert node.path == "/home/user/.bashrc"
        assert node.permission == "755"
        assert node.data == "export PATH=$PATH:/usr/local/bin"

    def test_creation_with_empty_data(self) -> None:
        node = DotfileNode(path="/home/.vimrc", permission="644", data="")
        assert node.data == ""

    def test_creation_with_various_permissions(self) -> None:
        for perm in ("755", "644", "600", "000", "777"):
            node = DotfileNode(path="/home/.test", permission=perm, data="")
            assert node.permission == perm


class TestDotfileNodeSerialization:
    """Tests for DotfileNode serialization."""

    def test_model_dump_json_has_all_fields(self) -> None:
        node = DotfileNode(
            path="/home/.bashrc",
            permission="755",
            data="content",
        )
        parsed = json.loads(node.model_dump_json())
        assert "path" in parsed
        assert "permission" in parsed
        assert "data" in parsed
        assert parsed["path"] == "/home/.bashrc"
        assert parsed["permission"] == "755"
        assert parsed["data"] == "content"

    def test_round_trip_preserves_all_fields(self) -> None:
        node = DotfileNode(
            path="/home/user/.bashrc",
            permission="644",
            data="export LANG=en_US.UTF-8\nexport PATH=$PATH:/usr/local/bin",
        )
        json_str = node.model_dump_json()
        restored = DotfileNode.model_validate_json(json_str)
        assert restored.path == node.path
        assert restored.permission == node.permission
        assert restored.data == node.data

    def test_round_trip_with_empty_data(self) -> None:
        node = DotfileNode(path="/home/.vimrc", permission="644", data="")
        json_str = node.model_dump_json()
        restored = DotfileNode.model_validate_json(json_str)
        assert restored.path == node.path
        assert restored.permission == node.permission
        assert restored.data == ""

    def test_round_trip_with_multiline_data(self) -> None:
        data = "line1\nline2\nline3"
        node = DotfileNode(path="/home/.profile", permission="755", data=data)
        json_str = node.model_dump_json()
        restored = DotfileNode.model_validate_json(json_str)
        assert restored.data == data


class TestDotfileListPayload:
    """Tests for DotfileListPayload model."""

    def test_creation_with_empty_list(self) -> None:
        payload = DotfileListPayload(items=[])
        assert payload.items == []

    def test_creation_with_single_item(self) -> None:
        items = [DotfileNode(path="/home/.bashrc", permission="755", data="content")]
        payload = DotfileListPayload(items=items)
        assert len(payload.items) == 1
        assert payload.items[0].path == "/home/.bashrc"

    def test_creation_with_multiple_items(self) -> None:
        items = [
            DotfileNode(path="/home/.bashrc", permission="755", data="content1"),
            DotfileNode(path="/home/.vimrc", permission="644", data="content2"),
        ]
        payload = DotfileListPayload(items=items)
        assert len(payload.items) == 2
        assert payload.items[0].path == "/home/.bashrc"
        assert payload.items[1].path == "/home/.vimrc"

    def test_round_trip_with_items(self) -> None:
        items = [
            DotfileNode(path="/home/.bashrc", permission="755", data="content"),
        ]
        payload = DotfileListPayload(items=items)
        json_str = payload.model_dump_json()
        restored = DotfileListPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].path == "/home/.bashrc"
        assert restored.items[0].permission == "755"
        assert restored.items[0].data == "content"

    def test_round_trip_with_empty_items(self) -> None:
        payload = DotfileListPayload(items=[])
        json_str = payload.model_dump_json()
        restored = DotfileListPayload.model_validate_json(json_str)
        assert restored.items == []

    def test_items_are_nested_in_json(self) -> None:
        items = [DotfileNode(path="/home/.bashrc", permission="644", data="")]
        payload = DotfileListPayload(items=items)
        parsed = json.loads(payload.model_dump_json())
        assert "items" in parsed
        assert isinstance(parsed["items"], list)
        assert len(parsed["items"]) == 1
        assert parsed["items"][0]["path"] == "/home/.bashrc"

    def test_nested_items_preserve_all_fields_in_json(self) -> None:
        items = [
            DotfileNode(path="/home/.bashrc", permission="755", data="some content"),
            DotfileNode(path="/home/.vimrc", permission="644", data=""),
        ]
        payload = DotfileListPayload(items=items)
        parsed = json.loads(payload.model_dump_json())
        assert parsed["items"][0]["permission"] == "755"
        assert parsed["items"][0]["data"] == "some content"
        assert parsed["items"][1]["permission"] == "644"
        assert parsed["items"][1]["data"] == ""


class TestDeleteDotfilePayload:
    """Tests for DeleteDotfilePayload model."""

    def test_creation_with_success_true(self) -> None:
        payload = DeleteDotfilePayload(success=True)
        assert payload.success is True

    def test_creation_with_success_false(self) -> None:
        payload = DeleteDotfilePayload(success=False)
        assert payload.success is False

    def test_round_trip_success_true(self) -> None:
        payload = DeleteDotfilePayload(success=True)
        json_str = payload.model_dump_json()
        restored = DeleteDotfilePayload.model_validate_json(json_str)
        assert restored.success is True

    def test_round_trip_success_false(self) -> None:
        payload = DeleteDotfilePayload(success=False)
        json_str = payload.model_dump_json()
        restored = DeleteDotfilePayload.model_validate_json(json_str)
        assert restored.success is False

    def test_json_has_success_field(self) -> None:
        payload = DeleteDotfilePayload(success=True)
        parsed = json.loads(payload.model_dump_json())
        assert "success" in parsed
        assert parsed["success"] is True


class TestBootstrapScriptNode:
    """Tests for BootstrapScriptNode model."""

    def test_creation_with_script(self) -> None:
        node = BootstrapScriptNode(script="#!/bin/bash\necho hello")
        assert node.script == "#!/bin/bash\necho hello"

    def test_creation_with_empty_script(self) -> None:
        node = BootstrapScriptNode(script="")
        assert node.script == ""

    def test_round_trip(self) -> None:
        node = BootstrapScriptNode(script="#!/bin/bash\nexport PATH=$PATH:/opt/bin")
        json_str = node.model_dump_json()
        restored = BootstrapScriptNode.model_validate_json(json_str)
        assert restored.script == node.script

    def test_round_trip_multiline_script(self) -> None:
        script = "#!/bin/bash\nset -e\nexport LANG=en_US.UTF-8\necho done"
        node = BootstrapScriptNode(script=script)
        json_str = node.model_dump_json()
        restored = BootstrapScriptNode.model_validate_json(json_str)
        assert restored.script == script

    def test_json_has_script_field(self) -> None:
        node = BootstrapScriptNode(script="#!/bin/bash")
        parsed = json.loads(node.model_dump_json())
        assert "script" in parsed
        assert parsed["script"] == "#!/bin/bash"


class TestEmptyPayloads:
    """Tests for empty payload models."""

    def test_create_dotfile_payload_creation(self) -> None:
        payload = CreateDotfilePayload()
        assert payload is not None

    def test_create_dotfile_payload_round_trip(self) -> None:
        payload = CreateDotfilePayload()
        json_str = payload.model_dump_json()
        restored = CreateDotfilePayload.model_validate_json(json_str)
        assert restored is not None

    def test_update_dotfile_payload_creation(self) -> None:
        payload = UpdateDotfilePayload()
        assert payload is not None

    def test_update_dotfile_payload_round_trip(self) -> None:
        payload = UpdateDotfilePayload()
        json_str = payload.model_dump_json()
        restored = UpdateDotfilePayload.model_validate_json(json_str)
        assert restored is not None

    def test_update_bootstrap_script_payload_creation(self) -> None:
        payload = UpdateBootstrapScriptPayload()
        assert payload is not None

    def test_update_bootstrap_script_payload_round_trip(self) -> None:
        payload = UpdateBootstrapScriptPayload()
        json_str = payload.model_dump_json()
        restored = UpdateBootstrapScriptPayload.model_validate_json(json_str)
        assert restored is not None
