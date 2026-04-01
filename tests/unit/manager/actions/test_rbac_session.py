"""Tests for SESSION RBAC action declarations."""

import pytest

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)
from ai.backend.manager.actions.action.rbac_session import (
    SessionCreateRBACAction,
    SessionGetRBACAction,
    SessionGrantAllRBACAction,
    SessionGrantHardDeleteRBACAction,
    SessionGrantReadRBACAction,
    SessionGrantUpdateRBACAction,
    SessionHardDeleteRBACAction,
    SessionSearchRBACAction,
    SessionUpdateRBACAction,
)

ALL_SESSION_ACTIONS: list[type[BaseRBACAction]] = [
    SessionCreateRBACAction,
    SessionGetRBACAction,
    SessionSearchRBACAction,
    SessionUpdateRBACAction,
    SessionHardDeleteRBACAction,
    SessionGrantAllRBACAction,
    SessionGrantReadRBACAction,
    SessionGrantUpdateRBACAction,
    SessionGrantHardDeleteRBACAction,
]


class TestSessionRBACActionInheritance:
    @pytest.mark.parametrize("action_cls", ALL_SESSION_ACTIONS)
    def test_inherits_from_base_rbac_action(self, action_cls: type[BaseRBACAction]) -> None:
        assert issubclass(action_cls, BaseRBACAction)

    @pytest.mark.parametrize("action_cls", ALL_SESSION_ACTIONS)
    def test_element_type_is_session(self, action_cls: type[BaseRBACAction]) -> None:
        perm = action_cls.required_permission()
        assert perm.element_type == RBACElementType.SESSION


class TestSessionRBACActionUniqueness:
    def test_action_names_are_unique(self) -> None:
        names = [cls.action_name() for cls in ALL_SESSION_ACTIONS]
        assert len(names) == len(set(names))


class TestSessionRBACActionExclusions:
    def test_no_soft_delete_action(self) -> None:
        action_names = {cls.action_name() for cls in ALL_SESSION_ACTIONS}
        assert RBACActionName.SOFT_DELETE not in action_names

    def test_no_grant_soft_delete_action(self) -> None:
        action_names = {cls.action_name() for cls in ALL_SESSION_ACTIONS}
        assert RBACActionName.GRANT_SOFT_DELETE not in action_names

    def test_no_soft_delete_operation(self) -> None:
        operations = {cls.required_permission().operation for cls in ALL_SESSION_ACTIONS}
        assert OperationType.SOFT_DELETE not in operations

    def test_no_grant_soft_delete_operation(self) -> None:
        operations = {cls.required_permission().operation for cls in ALL_SESSION_ACTIONS}
        assert OperationType.GRANT_SOFT_DELETE not in operations


class TestSessionRBACActionMapping:
    @pytest.mark.parametrize(
        ("action_cls", "expected_name", "expected_operation"),
        [
            (SessionCreateRBACAction, RBACActionName.CREATE, OperationType.CREATE),
            (SessionGetRBACAction, RBACActionName.GET, OperationType.READ),
            (SessionSearchRBACAction, RBACActionName.SEARCH, OperationType.READ),
            (SessionUpdateRBACAction, RBACActionName.UPDATE, OperationType.UPDATE),
            (SessionHardDeleteRBACAction, RBACActionName.HARD_DELETE, OperationType.HARD_DELETE),
            (SessionGrantAllRBACAction, RBACActionName.GRANT_ALL, OperationType.GRANT_ALL),
            (SessionGrantReadRBACAction, RBACActionName.GRANT_READ, OperationType.GRANT_READ),
            (SessionGrantUpdateRBACAction, RBACActionName.GRANT_UPDATE, OperationType.GRANT_UPDATE),
            (
                SessionGrantHardDeleteRBACAction,
                RBACActionName.GRANT_HARD_DELETE,
                OperationType.GRANT_HARD_DELETE,
            ),
        ],
    )
    def test_action_name_and_operation(
        self,
        action_cls: type[BaseRBACAction],
        expected_name: RBACActionName,
        expected_operation: OperationType,
    ) -> None:
        assert action_cls.action_name() == expected_name
        perm = action_cls.required_permission()
        assert perm.element_type == RBACElementType.SESSION
        assert perm.operation == expected_operation


class TestGetEntityValidOperations:
    def test_aggregation_produces_session_entry(self) -> None:
        result: dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]] = {}
        for action_cls in ALL_SESSION_ACTIONS:
            perm = action_cls.required_permission()
            actions = result.setdefault(perm.element_type, {})
            actions[action_cls.action_name()] = perm

        assert RBACElementType.SESSION in result
        session_actions = result[RBACElementType.SESSION]
        assert len(session_actions) == 9

    def test_aggregation_maps_correct_operations(self) -> None:
        result: dict[RBACElementType, dict[RBACActionName, RBACRequiredPermission]] = {}
        for action_cls in ALL_SESSION_ACTIONS:
            perm = action_cls.required_permission()
            actions = result.setdefault(perm.element_type, {})
            actions[action_cls.action_name()] = perm

        session_actions = result[RBACElementType.SESSION]
        expected_operations = {
            RBACActionName.CREATE: OperationType.CREATE,
            RBACActionName.GET: OperationType.READ,
            RBACActionName.SEARCH: OperationType.READ,
            RBACActionName.UPDATE: OperationType.UPDATE,
            RBACActionName.HARD_DELETE: OperationType.HARD_DELETE,
            RBACActionName.GRANT_ALL: OperationType.GRANT_ALL,
            RBACActionName.GRANT_READ: OperationType.GRANT_READ,
            RBACActionName.GRANT_UPDATE: OperationType.GRANT_UPDATE,
            RBACActionName.GRANT_HARD_DELETE: OperationType.GRANT_HARD_DELETE,
        }
        for action_name, expected_op in expected_operations.items():
            assert session_actions[action_name].operation == expected_op
