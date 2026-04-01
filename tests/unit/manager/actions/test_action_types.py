"""Tests for the action type system: ActionOperationType, EntityType, and enum enforcement."""

from ai.backend.common.data.permission.types import EntityType, OperationType
from ai.backend.manager.actions.action.base import BaseAction
from ai.backend.manager.actions.types import ActionOperationType

# Import representative concrete action classes across different entity types
# and operation types to verify enum usage at runtime.
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.object_storage.actions.create import CreateObjectStorageAction
from ai.backend.manager.services.object_storage.actions.update import UpdateObjectStorageAction
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.user.actions.purge_user import PurgeUserAction
from ai.backend.manager.services.vfs_storage.actions.delete import DeleteVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction

_REPRESENTATIVE_ACTION_CLASSES: list[type[BaseAction]] = [
    GetArtifactAction,
    GetVFSStorageAction,
    SearchSessionsAction,
    CreateObjectStorageAction,
    UpdateObjectStorageAction,
    DeleteVFSStorageAction,
    PurgeUserAction,
]


class TestActionOperationType:
    def test_has_exactly_six_values(self) -> None:
        values = list(ActionOperationType)
        assert len(values) == 6
        expected = {"get", "search", "create", "update", "delete", "purge"}
        assert {v.value for v in values} == expected

    def test_to_permission_operation_mapping(self) -> None:
        assert ActionOperationType.GET.to_permission_operation() == OperationType.READ
        assert ActionOperationType.SEARCH.to_permission_operation() == OperationType.READ
        assert ActionOperationType.CREATE.to_permission_operation() == OperationType.CREATE
        assert ActionOperationType.UPDATE.to_permission_operation() == OperationType.UPDATE
        assert ActionOperationType.DELETE.to_permission_operation() == OperationType.SOFT_DELETE
        assert ActionOperationType.PURGE.to_permission_operation() == OperationType.HARD_DELETE

    def test_all_values_are_unique(self) -> None:
        values = [v.value for v in ActionOperationType]
        assert len(values) == len(set(values))

    def test_is_str_subclass(self) -> None:
        for v in ActionOperationType:
            assert isinstance(v, str)


class TestEntityType:
    def test_all_values_are_unique(self) -> None:
        values = [v.value for v in EntityType]
        assert len(values) == len(set(values))

    def test_scope_types_returns_original_three(self) -> None:
        scope_types = EntityType._scope_types()
        assert scope_types == {EntityType.USER, EntityType.PROJECT, EntityType.DOMAIN}

    def test_resource_types_returns_original_nine(self) -> None:
        resource_types = EntityType._resource_types()
        expected = {
            EntityType.VFOLDER,
            EntityType.IMAGE,
            EntityType.SESSION,
            EntityType.ARTIFACT,
            EntityType.ARTIFACT_REGISTRY,
            EntityType.APP_CONFIG,
            EntityType.NOTIFICATION_CHANNEL,
            EntityType.NOTIFICATION_RULE,
            EntityType.MODEL_DEPLOYMENT,
        }
        assert resource_types == expected
        assert len(resource_types) == 9

    def test_scope_and_resource_types_no_overlap(self) -> None:
        scope_types = EntityType._scope_types()
        resource_types = EntityType._resource_types()
        assert scope_types.isdisjoint(resource_types)

    def test_is_str_subclass(self) -> None:
        for v in EntityType:
            assert isinstance(v, str)


class TestAllActionClassesUseEnums:
    """Verify that representative concrete action classes return proper enum types.

    These tests cover all six ActionOperationType values (GET, SEARCH, CREATE,
    UPDATE, DELETE, PURGE) via representative concrete action classes.
    """

    def test_entity_type_returns_enum(self) -> None:
        for cls in _REPRESENTATIVE_ACTION_CLASSES:
            result = cls.entity_type()
            assert isinstance(result, EntityType), (
                f"{cls.__name__}.entity_type() returned {type(result).__name__} "
                f"({result!r}), expected EntityType"
            )

    def test_operation_type_returns_enum(self) -> None:
        for cls in _REPRESENTATIVE_ACTION_CLASSES:
            result = cls.operation_type()
            assert isinstance(result, ActionOperationType), (
                f"{cls.__name__}.operation_type() returned {type(result).__name__} "
                f"({result!r}), expected ActionOperationType"
            )

    def test_covers_all_operation_types(self) -> None:
        """Ensure the representative classes cover all six ActionOperationType values."""
        covered = {cls.operation_type() for cls in _REPRESENTATIVE_ACTION_CLASSES}
        assert covered == set(ActionOperationType), (
            f"Not all ActionOperationType values are covered. "
            f"Missing: {set(ActionOperationType) - covered}"
        )
