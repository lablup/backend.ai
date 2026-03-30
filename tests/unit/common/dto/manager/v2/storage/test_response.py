"""Tests for ai.backend.common.dto.manager.v2.storage.response module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.storage.response import (
    GetVFSStoragePayload,
    ListVFSStoragePayload,
    VFSStorageNode,
)


def _make_node(name: str = "nfs01") -> VFSStorageNode:
    return VFSStorageNode(
        name=name,
        base_path="/mnt/nfs/data",
        host="storage.example.com",
    )


class TestVFSStorageNode:
    """Tests for VFSStorageNode model."""

    def test_creation(self) -> None:
        node = _make_node()
        assert node.name == "nfs01"
        assert node.base_path == "/mnt/nfs/data"
        assert node.host == "storage.example.com"

    def test_round_trip(self) -> None:
        node = _make_node()
        restored = VFSStorageNode.model_validate_json(node.model_dump_json())
        assert restored.name == "nfs01"
        assert restored.base_path == "/mnt/nfs/data"
        assert restored.host == "storage.example.com"

    def test_different_storage_names(self) -> None:
        node = _make_node("cephfs-01")
        assert node.name == "cephfs-01"

    def test_model_dump_has_all_fields(self) -> None:
        node = _make_node()
        data = node.model_dump()
        assert "name" in data
        assert "base_path" in data
        assert "host" in data


class TestGetVFSStoragePayload:
    """Tests for GetVFSStoragePayload model."""

    def test_creation(self) -> None:
        node = _make_node()
        payload = GetVFSStoragePayload(storage=node)
        assert payload.storage.name == "nfs01"

    def test_round_trip(self) -> None:
        node = _make_node("lustre-01")
        payload = GetVFSStoragePayload(storage=node)
        restored = GetVFSStoragePayload.model_validate_json(payload.model_dump_json())
        assert restored.storage.name == "lustre-01"
        assert restored.storage.base_path == "/mnt/nfs/data"


class TestListVFSStoragePayload:
    """Tests for ListVFSStoragePayload model."""

    def test_creation_with_multiple_storages(self) -> None:
        nodes = [_make_node("nfs01"), _make_node("nfs02"), _make_node("cephfs")]
        payload = ListVFSStoragePayload(storages=nodes)
        assert len(payload.storages) == 3

    def test_empty_list(self) -> None:
        payload = ListVFSStoragePayload(storages=[])
        assert payload.storages == []

    def test_round_trip_with_multiple_nodes(self) -> None:
        nodes = [_make_node("nfs01"), _make_node("nfs02")]
        payload = ListVFSStoragePayload(storages=nodes)
        restored = ListVFSStoragePayload.model_validate_json(payload.model_dump_json())
        assert len(restored.storages) == 2
        assert restored.storages[0].name == "nfs01"
        assert restored.storages[1].name == "nfs02"

    def test_round_trip_empty_list(self) -> None:
        payload = ListVFSStoragePayload(storages=[])
        restored = ListVFSStoragePayload.model_validate_json(payload.model_dump_json())
        assert restored.storages == []

    def test_storage_fields_preserved(self) -> None:
        node = VFSStorageNode(name="special", base_path="/tmp/data", host="host01")
        payload = ListVFSStoragePayload(storages=[node])
        restored = ListVFSStoragePayload.model_validate_json(payload.model_dump_json())
        assert restored.storages[0].host == "host01"
