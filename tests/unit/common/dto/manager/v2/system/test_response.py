"""Tests for ai.backend.common.dto.manager.v2.system.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.system.response import SystemVersionNode


class TestSystemVersionNode:
    """Tests for SystemVersionNode model creation and serialization."""

    def test_creation_with_version_and_manager(self) -> None:
        node = SystemVersionNode(version="v2.0", manager="23.09.0")
        assert node.version == "v2.0"
        assert node.manager == "23.09.0"

    def test_version_field_is_string(self) -> None:
        node = SystemVersionNode(version="v3.1", manager="24.03.0")
        assert isinstance(node.version, str)

    def test_manager_field_is_string(self) -> None:
        node = SystemVersionNode(version="v2.0", manager="23.09.5")
        assert isinstance(node.manager, str)

    def test_round_trip_preserves_version(self) -> None:
        node = SystemVersionNode(version="v2.0", manager="23.09.0")
        json_str = node.model_dump_json()
        restored = SystemVersionNode.model_validate_json(json_str)
        assert restored.version == node.version

    def test_round_trip_preserves_manager(self) -> None:
        node = SystemVersionNode(version="v2.0", manager="23.09.0")
        json_str = node.model_dump_json()
        restored = SystemVersionNode.model_validate_json(json_str)
        assert restored.manager == node.manager

    def test_round_trip_preserves_all_fields(self) -> None:
        node = SystemVersionNode(version="v2.1", manager="24.03.1")
        json_str = node.model_dump_json()
        restored = SystemVersionNode.model_validate_json(json_str)
        assert restored.version == node.version
        assert restored.manager == node.manager

    def test_json_has_version_field(self) -> None:
        node = SystemVersionNode(version="v2.0", manager="23.09.0")
        parsed = json.loads(node.model_dump_json())
        assert "version" in parsed
        assert parsed["version"] == "v2.0"

    def test_json_has_manager_field(self) -> None:
        node = SystemVersionNode(version="v2.0", manager="23.09.0")
        parsed = json.loads(node.model_dump_json())
        assert "manager" in parsed
        assert parsed["manager"] == "23.09.0"

    def test_json_has_exactly_expected_fields(self) -> None:
        node = SystemVersionNode(version="v2.0", manager="23.09.0")
        parsed = json.loads(node.model_dump_json())
        assert set(parsed.keys()) == {"version", "manager"}

    def test_creation_from_dict(self) -> None:
        data = {"version": "v2.0", "manager": "23.09.0"}
        node = SystemVersionNode.model_validate(data)
        assert node.version == "v2.0"
        assert node.manager == "23.09.0"

    def test_different_version_strings(self) -> None:
        node = SystemVersionNode(version="v1.0.0-alpha", manager="24.09.0.dev")
        assert node.version == "v1.0.0-alpha"
        assert node.manager == "24.09.0.dev"
