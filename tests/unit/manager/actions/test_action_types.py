"""Tests for the action type system: ActionOperationType, EntityType, and enum enforcement."""

from ai.backend.common.data.permission.types import EntityType, OperationType, Permission
from ai.backend.manager.actions.action.base import BaseAction
from ai.backend.manager.actions.types import ActionOperationType

# Import representative concrete action classes across different entity types
# and operation types to verify enum usage at runtime.
from ai.backend.manager.services.agent.actions.handle_heartbeat import HandleHeartbeatAction
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction
from ai.backend.manager.services.agent.actions.watcher_agent_start import WatcherAgentStartAction
from ai.backend.manager.services.auth.actions.authorize import AuthorizeAction
from ai.backend.manager.services.auth.actions.get_role import GetRoleAction
from ai.backend.manager.services.auth.actions.logout import LogoutAction
from ai.backend.manager.services.permission_contoller.actions.purge_role import PurgeRoleAction

# Legacy-family actions only. The v2 families answer with
# ``ai.backend.common.data.entity.types.EntityType``, a distinct NewType, so mixing
# them in would conflate two type systems rather than test either one.
_REPRESENTATIVE_ACTION_CLASSES: list[type[BaseAction]] = [
    AuthorizeAction,
    GetRoleAction,
    HandleHeartbeatAction,
    LogoutAction,
    PurgeRoleAction,
    SearchAgentsAction,
    WatcherAgentStartAction,
]


class TestActionOperationType:
    def test_has_exactly_nine_values(self) -> None:
        values = list(ActionOperationType)
        assert len(values) == 9
        expected = {
            "get",
            "search",
            "create",
            "update",
            "upsert",
            "delete",
            "purge",
            "restore",
            "lookup",
        }
        assert {v.value for v in values} == expected

    def test_to_permission_operation_mapping(self) -> None:
        assert ActionOperationType.GET.to_permission_operation() == OperationType.READ
        assert ActionOperationType.SEARCH.to_permission_operation() == OperationType.READ
        assert ActionOperationType.LOOKUP.to_permission_operation() == OperationType.READ
        assert ActionOperationType.CREATE.to_permission_operation() == OperationType.CREATE
        assert ActionOperationType.UPDATE.to_permission_operation() == OperationType.UPDATE
        assert ActionOperationType.UPSERT.to_permission_operation() == OperationType.CREATE
        assert ActionOperationType.DELETE.to_permission_operation() == OperationType.SOFT_DELETE
        assert ActionOperationType.PURGE.to_permission_operation() == OperationType.HARD_DELETE
        assert ActionOperationType.RESTORE.to_permission_operation() == OperationType.SOFT_DELETE

    def test_to_permission_mapping(self) -> None:
        assert ActionOperationType.GET.to_permission() == Permission.READ
        assert ActionOperationType.SEARCH.to_permission() == Permission.READ
        assert ActionOperationType.LOOKUP.to_permission() == Permission.READ
        assert ActionOperationType.CREATE.to_permission() == Permission.CREATE
        assert ActionOperationType.UPDATE.to_permission() == Permission.UPDATE
        assert ActionOperationType.DELETE.to_permission() == Permission.SOFT_DELETE
        assert ActionOperationType.PURGE.to_permission() == Permission.HARD_DELETE
        assert ActionOperationType.RESTORE.to_permission() == Permission.SOFT_DELETE

    def test_upsert_requires_both_create_and_update(self) -> None:
        """An upsert may insert or overwrite, so neither bit alone is sufficient."""
        required = ActionOperationType.UPSERT.to_permission()
        assert required == Permission.CREATE | Permission.UPDATE
        assert not Permission.CREATE.covers(required)
        assert not Permission.UPDATE.covers(required)
        assert (Permission.CREATE | Permission.UPDATE).covers(required)

    def test_to_permission_covers_every_operation(self) -> None:
        for op in ActionOperationType:
            assert op.to_permission() != Permission.NONE

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

    def test_resource_types_returns_expected_set(self) -> None:
        resource_types = EntityType._resource_types()
        expected = {
            EntityType.VFOLDER,
            EntityType.IMAGE,
            EntityType.SESSION,
            EntityType.ARTIFACT,
            EntityType.ARTIFACT_REGISTRY,
            EntityType.APP_CONFIG_FRAGMENT,
            EntityType.NOTIFICATION_CHANNEL,
            EntityType.NOTIFICATION_RULE,
            EntityType.MODEL_DEPLOYMENT,
            EntityType.MODEL_CARD,
        }
        assert resource_types == expected
        assert len(resource_types) == 10

    def test_scope_and_resource_types_no_overlap(self) -> None:
        scope_types = EntityType._scope_types()
        resource_types = EntityType._resource_types()
        assert scope_types.isdisjoint(resource_types)

    def test_is_str_subclass(self) -> None:
        for v in EntityType:
            assert isinstance(v, str)


class TestAllActionClassesUseEnums:
    """Verify that representative concrete action classes return proper enum types.

    These tests cover the operations concrete actions declare today (GET, SEARCH,
    CREATE, UPDATE, DELETE, PURGE) via representative concrete action classes.
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
        """Ensure the representative classes cover every declarable operation.

        ``UPSERT`` is excluded: the upsert actions declare ``CREATE`` today, so
        nothing can stand for it. ``LOOKUP`` and ``RESTORE`` are excluded because no
        legacy action declares them, and every class here is a legacy one.
        """
        expected = set(ActionOperationType) - {
            ActionOperationType.UPSERT,
            ActionOperationType.LOOKUP,
            ActionOperationType.RESTORE,
        }
        covered = {cls.operation_type() for cls in _REPRESENTATIVE_ACTION_CLASSES}
        assert covered == expected, (
            f"Not all ActionOperationType values are covered. Missing: {expected - covered}"
        )
