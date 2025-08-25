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
    def test_status_values(self):
        assert BgtaskStatus.STARTED == "bgtask_started"
        assert BgtaskStatus.UPDATED == "bgtask_updated"
        assert BgtaskStatus.DONE == "bgtask_done"
        assert BgtaskStatus.CANCELLED == "bgtask_cancelled"
        assert BgtaskStatus.FAILED == "bgtask_failed"
        assert BgtaskStatus.PARTIAL_SUCCESS == "bgtask_partial_success"

    def test_finished(self):
        assert BgtaskStatus.DONE.finished() is True
        assert BgtaskStatus.CANCELLED.finished() is True
        assert BgtaskStatus.FAILED.finished() is True
        assert BgtaskStatus.PARTIAL_SUCCESS.finished() is True

        assert BgtaskStatus.STARTED.finished() is False
        assert BgtaskStatus.UPDATED.finished() is False

    def test_string_conversion(self):
        assert str(BgtaskStatus.STARTED) == "bgtask_started"
        assert str(BgtaskStatus.DONE) == "bgtask_done"


class TestTaskName:
    def test_task_names(self):
        assert TaskName.CLONE_VFOLDER == "clone_vfolder"
        assert TaskName.PUSH_IMAGE == "push_image"

    def test_string_conversion(self):
        assert str(TaskName.CLONE_VFOLDER) == "clone_vfolder"
        assert str(TaskName.PUSH_IMAGE) == "push_image"


class TestTaskID:
    def test_task_id_creation(self):
        uuid_value = uuid.uuid4()
        task_id = TaskID(uuid_value)
        assert task_id == uuid_value
        assert isinstance(task_id, uuid.UUID)

    def test_task_id_equality(self):
        uuid_value = uuid.uuid4()
        task_id1 = TaskID(uuid_value)
        task_id2 = TaskID(uuid_value)
        assert task_id1 == task_id2

    def test_task_id_hash(self):
        uuid_value = uuid.uuid4()
        task_id = TaskID(uuid_value)
        assert hash(task_id) == hash(uuid_value)

        task_ids = {task_id}
        assert task_id in task_ids


class TestBackgroundTaskMetadata:
    def test_create(self):
        task_id = TaskID(uuid.uuid4())
        metadata = BackgroundTaskMetadata.create(
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

    def test_create_with_tags(self):
        task_id = TaskID(uuid.uuid4())
        tags = ["tag1", "tag2", "tag3"]
        metadata = BackgroundTaskMetadata.create(
            task_id=task_id,
            task_name=TaskName.PUSH_IMAGE,
            body={"data": "test"},
            server_id="server-2",
            tags=tags,
        )

        assert metadata.tags == {"tag1", "tag2", "tag3"}

    def test_create_with_none_tags(self):
        task_id = TaskID(uuid.uuid4())
        metadata = BackgroundTaskMetadata.create(
            task_id=task_id,
            task_name=TaskName.CLONE_VFOLDER,
            body={},
            server_id="server-3",
            tags=None,
        )

        assert metadata.tags == set()

    def test_to_json(self):
        task_id = TaskID(uuid.uuid4())
        metadata = BackgroundTaskMetadata.create(
            task_id=task_id,
            task_name=TaskName.CLONE_VFOLDER,
            body={"test": "data", "number": 42},
            server_id="server-1",
            tags=["tag1", "tag2"],
        )

        json_str = metadata.to_json()
        data = json.loads(json_str)

        assert data["task_id"] == str(task_id)
        assert data["task_name"] == "clone_vfolder"
        assert data["body"]["test"] == "data"
        assert data["body"]["number"] == 42
        assert data["server_id"] == "server-1"
        assert set(data["tags"]) == {"tag1", "tag2"}

    def test_from_json(self):
        task_id = TaskID(uuid.uuid4())
        json_data = json.dumps({
            "task_id": str(task_id),
            "task_name": "push_image",
            "body": {"key": "value", "count": 10},
            "server_id": "server-2",
            "tags": ["tag3", "tag4"],
        })

        metadata = BackgroundTaskMetadata.from_json(json_data)

        assert str(metadata.task_id) == str(task_id)
        assert metadata.task_name == TaskName.PUSH_IMAGE
        assert metadata.body == {"key": "value", "count": 10}
        assert metadata.server_id == "server-2"
        assert metadata.tags == {"tag3", "tag4"}

    def test_from_json_bytes(self):
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

    def test_round_trip_serialization(self):
        task_id = TaskID(uuid.uuid4())
        original = BackgroundTaskMetadata.create(
            task_id=task_id,
            task_name=TaskName.CLONE_VFOLDER,
            body={"complex": {"nested": "data"}, "list": [1, 2, 3]},
            server_id="server-1",
            tags=["tag1", "tag2", "tag3"],
        )

        json_str = original.to_json()
        restored = BackgroundTaskMetadata.from_json(json_str)

        assert str(restored.task_id) == str(original.task_id)
        assert restored.task_name == original.task_name
        assert restored.body == original.body
        assert restored.server_id == original.server_id
        assert restored.tags == original.tags

    def test_modify_server_id(self):
        task_id = TaskID(uuid.uuid4())
        metadata = BackgroundTaskMetadata.create(
            task_id=task_id,
            task_name=TaskName.CLONE_VFOLDER,
            body={},
            server_id="old-server",
        )

        metadata.server_id = "new-server"
        assert metadata.server_id == "new-server"

    def test_empty_body(self):
        task_id = TaskID(uuid.uuid4())
        metadata = BackgroundTaskMetadata.create(
            task_id=task_id,
            task_name=TaskName.PUSH_IMAGE,
            body={},
            server_id="server-1",
        )

        assert metadata.body == {}
        json_str = metadata.to_json()
        restored = BackgroundTaskMetadata.from_json(json_str)
        assert restored.body == {}
