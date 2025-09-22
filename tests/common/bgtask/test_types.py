from __future__ import annotations

import json
import uuid

from ai.backend.common.bgtask.types import (
    BackgroundTaskMetadata,
    BgtaskStatus,
    TaskID,
    TaskName,
)


class TestBgtaskStatus:
    def test_status_values(self) -> None:
        assert BgtaskStatus.STARTED == "bgtask_started"
        assert BgtaskStatus.UPDATED == "bgtask_updated"
        assert BgtaskStatus.DONE == "bgtask_done"
        assert BgtaskStatus.CANCELLED == "bgtask_cancelled"
        assert BgtaskStatus.FAILED == "bgtask_failed"
        assert BgtaskStatus.PARTIAL_SUCCESS == "bgtask_partial_success"

    def test_finished(self) -> None:
        assert BgtaskStatus.DONE.finished() is True
        assert BgtaskStatus.CANCELLED.finished() is True
        assert BgtaskStatus.FAILED.finished() is True
        assert BgtaskStatus.PARTIAL_SUCCESS.finished() is True

        assert BgtaskStatus.STARTED.finished() is False
        assert BgtaskStatus.UPDATED.finished() is False

    def test_string_conversion(self) -> None:
        assert str(BgtaskStatus.STARTED) == "bgtask_started"
        assert str(BgtaskStatus.DONE) == "bgtask_done"


class TestTaskName:
    def test_task_names(self) -> None:
        assert TaskName.CLONE_VFOLDER == "clone_vfolder"
        assert TaskName.PUSH_IMAGE == "push_image"

    def test_string_conversion(self) -> None:
        assert str(TaskName.CLONE_VFOLDER) == "clone_vfolder"
        assert str(TaskName.PUSH_IMAGE) == "push_image"


class TestTaskID:
    def test_task_id_creation(self) -> None:
        uuid_value = uuid.uuid4()
        task_id = TaskID(uuid_value)
        assert task_id == uuid_value
        assert isinstance(task_id, uuid.UUID)

    def test_task_id_equality(self) -> None:
        uuid_value = uuid.uuid4()
        task_id1 = TaskID(uuid_value)
        task_id2 = TaskID(uuid_value)
        assert task_id1 == task_id2

    def test_task_id_hash(self) -> None:
        uuid_value = uuid.uuid4()
        task_id = TaskID(uuid_value)
        assert hash(task_id) == hash(uuid_value)

        task_ids = {task_id}
        assert task_id in task_ids


class TestBackgroundTaskMetadata:
    def test_create(self) -> None:
        task_id = TaskID(uuid.uuid4())
        metadata = BackgroundTaskMetadata(
            task_id=task_id,
            task_name=TaskName.CLONE_VFOLDER,
            body={"key": "value"},
            server_id="server-1",
        )

        assert metadata.task_id == task_id
        assert metadata.task_name == TaskName.CLONE_VFOLDER
        assert metadata.body == {"key": "value"}
        assert metadata.server_id == "server-1"
        assert metadata.tags == set()

    def test_create_with_tags(self) -> None:
        task_id = TaskID(uuid.uuid4())
        tags = {"tag1", "tag2", "tag3"}
        metadata = BackgroundTaskMetadata(
            task_id=task_id,
            task_name=TaskName.PUSH_IMAGE,
            body={"data": "test"},
            server_id="server-2",
            tags=tags,
        )

        assert metadata.tags == {"tag1", "tag2", "tag3"}

    def test_create_with_none_tags(self) -> None:
        task_id = TaskID(uuid.uuid4())
        metadata = BackgroundTaskMetadata(
            task_id=task_id,
            task_name=TaskName.CLONE_VFOLDER,
            body={},
            server_id="server-3",
        )

        assert metadata.tags == set()

    def test_json_serialization_deserialization(self) -> None:
        # Test to_json and from_json together since they are a pair for DB storage
        task_id = TaskID(uuid.uuid4())
        original_metadata = BackgroundTaskMetadata(
            task_id=task_id,
            task_name=TaskName.CLONE_VFOLDER,
            body={"test": "data", "number": 42, "nested": {"key": "value"}},
            server_id="server-1",
            tags={"tag1", "tag2"},
        )

        # Serialize to JSON
        json_str = original_metadata.to_json()

        # Verify the JSON structure
        data = json.loads(json_str)
        assert data["task_id"] == str(task_id)
        assert data["task_name"] == "clone_vfolder"
        assert data["body"]["test"] == "data"
        assert data["body"]["number"] == 42
        assert data["server_id"] == "server-1"
        assert set(data["tags"]) == {"tag1", "tag2"}

        # Deserialize from JSON
        restored_metadata = BackgroundTaskMetadata.from_json(json_str)

        # Verify the restored object matches the original
        assert str(restored_metadata.task_id) == str(original_metadata.task_id)
        assert restored_metadata.task_name == original_metadata.task_name
        assert restored_metadata.body == original_metadata.body
        assert restored_metadata.server_id == original_metadata.server_id
        assert restored_metadata.tags == original_metadata.tags

    def test_json_serialization_with_bytes_input(self) -> None:
        # Test that from_json can handle bytes input (common in DB operations)
        task_id = TaskID(uuid.uuid4())
        json_data = json.dumps({
            "task_id": str(task_id),
            "task_name": "clone_vfolder",
            "body": {"data": "test"},
            "server_id": "server-3",
            "tags": [],
        }).encode("utf-8")

        metadata = BackgroundTaskMetadata.from_json(json_data)

        assert str(metadata.task_id) == str(task_id)
        assert metadata.task_name == TaskName.CLONE_VFOLDER
        assert metadata.body == {"data": "test"}
        assert metadata.server_id == "server-3"
        assert metadata.tags == set()

    def test_json_serialization_with_complex_data(self) -> None:
        # Test serialization/deserialization with more complex nested structures
        task_id = TaskID(uuid.uuid4())
        complex_body = {
            "nested": {"deeply": {"nested": "value"}},
            "list": [1, 2, 3],
            "mixed": [{"key": "value"}, {"another": "item"}],
            "boolean": True,
            "null": None,
        }

        original = BackgroundTaskMetadata(
            task_id=task_id,
            task_name=TaskName.PUSH_IMAGE,
            body=complex_body,
            server_id="server-complex",
            tags={"tag1", "tag2", "tag3"},
        )

        # Round-trip serialization
        json_str = original.to_json()
        restored = BackgroundTaskMetadata.from_json(json_str)

        assert str(restored.task_id) == str(original.task_id)
        assert restored.task_name == original.task_name
        assert restored.body == original.body
        assert restored.body["nested"]["deeply"]["nested"] == "value"
        assert restored.body["list"] == [1, 2, 3]
        assert restored.server_id == original.server_id
        assert restored.tags == original.tags
