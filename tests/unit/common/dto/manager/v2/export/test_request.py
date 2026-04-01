"""Tests for ai.backend.common.dto.manager.v2.export.request module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.export.request import (
    AuditLogExportCSVInput,
    AuditLogExportFilter,
    AuditLogExportOrder,
    AuditLogExportOrderField,
    KeypairExportCSVInput,
    ProjectExportCSVInput,
    ProjectExportFilter,
    ProjectExportOrder,
    ProjectExportOrderField,
    SessionExportCSVInput,
    SessionExportFilter,
    SessionExportOrder,
    SessionExportOrderField,
    UserExportCSVInput,
    UserExportFilter,
    UserExportOrder,
    UserExportOrderField,
)
from ai.backend.common.dto.manager.v2.export.types import OrderDirection


class TestUserExportCSVInput:
    """Tests for UserExportCSVInput model."""

    def test_creation_with_all_defaults(self) -> None:
        req = UserExportCSVInput()
        assert req.fields is None
        assert req.filter is None
        assert req.order is None
        assert req.encoding == "utf-8"

    def test_creation_with_explicit_fields(self) -> None:
        req = UserExportCSVInput(fields=["username", "email"])
        assert req.fields == ["username", "email"]

    def test_creation_with_filter(self) -> None:
        f = UserExportFilter(role=["admin"])
        req = UserExportCSVInput(filter=f)
        assert req.filter is not None
        assert req.filter.role == ["admin"]

    def test_creation_with_order(self) -> None:
        order = [UserExportOrder(field=UserExportOrderField.USERNAME)]
        req = UserExportCSVInput(order=order)
        assert req.order is not None
        assert len(req.order) == 1
        assert req.order[0].field == UserExportOrderField.USERNAME

    def test_encoding_default_utf8(self) -> None:
        req = UserExportCSVInput()
        assert req.encoding == "utf-8"

    def test_encoding_euc_kr(self) -> None:
        req = UserExportCSVInput(encoding="euc-kr")
        assert req.encoding == "euc-kr"

    def test_round_trip_serialization(self) -> None:
        req = UserExportCSVInput(
            fields=["username", "email"],
            filter=UserExportFilter(
                status=["active"],
            ),
            order=[
                UserExportOrder(
                    field=UserExportOrderField.CREATED_AT, direction=OrderDirection.DESC
                )
            ],
            encoding="utf-8",
        )
        json_data = req.model_dump_json()
        restored = UserExportCSVInput.model_validate_json(json_data)
        assert restored.fields == req.fields
        assert restored.filter is not None
        assert restored.filter.status == ["active"]
        assert restored.order is not None
        assert restored.order[0].field == UserExportOrderField.CREATED_AT
        assert restored.order[0].direction == OrderDirection.DESC


class TestUserExportOrderField:
    """Tests for UserExportOrderField StrEnum."""

    def test_username_value(self) -> None:
        assert UserExportOrderField.USERNAME.value == "username"

    def test_email_value(self) -> None:
        assert UserExportOrderField.EMAIL.value == "email"

    def test_created_at_value(self) -> None:
        assert UserExportOrderField.CREATED_AT.value == "created_at"

    def test_from_string(self) -> None:
        assert UserExportOrderField("email") is UserExportOrderField.EMAIL


class TestUserExportOrder:
    """Tests for UserExportOrder model."""

    def test_default_direction_is_asc(self) -> None:
        order = UserExportOrder(field=UserExportOrderField.USERNAME)
        assert order.direction == OrderDirection.ASC

    def test_explicit_desc_direction(self) -> None:
        order = UserExportOrder(field=UserExportOrderField.EMAIL, direction=OrderDirection.DESC)
        assert order.direction == OrderDirection.DESC


class TestSessionExportCSVInput:
    """Tests for SessionExportCSVInput model."""

    def test_creation_with_all_defaults(self) -> None:
        req = SessionExportCSVInput()
        assert req.fields is None
        assert req.filter is None
        assert req.order is None
        assert req.encoding == "utf-8"

    def test_creation_with_status_filter(self) -> None:
        f = SessionExportFilter(status=["RUNNING"])
        req = SessionExportCSVInput(filter=f)
        assert req.filter is not None
        assert req.filter.status == ["RUNNING"]

    def test_creation_with_multiple_statuses(self) -> None:
        f = SessionExportFilter(status=["RUNNING", "PENDING"])
        req = SessionExportCSVInput(filter=f)
        assert req.filter is not None
        assert req.filter.status is not None
        assert len(req.filter.status) == 2

    def test_creation_with_name_filter(self) -> None:
        name_filter = StringFilter.model_validate({"mode": "contains", "value": "test"})
        f = SessionExportFilter(name=name_filter)
        req = SessionExportCSVInput(filter=f)
        assert req.filter is not None
        assert req.filter.name is not None

    def test_round_trip_serialization(self) -> None:
        req = SessionExportCSVInput(
            fields=["name", "status"],
            filter=SessionExportFilter(status=["RUNNING"]),
            order=[SessionExportOrder(field=SessionExportOrderField.CREATED_AT)],
        )
        json_data = req.model_dump_json()
        restored = SessionExportCSVInput.model_validate_json(json_data)
        assert restored.fields == req.fields
        assert restored.filter is not None
        assert restored.filter.status == ["RUNNING"]
        assert restored.order is not None
        assert restored.order[0].field == SessionExportOrderField.CREATED_AT


class TestSessionExportOrderField:
    """Tests for SessionExportOrderField StrEnum."""

    def test_name_value(self) -> None:
        assert SessionExportOrderField.NAME.value == "name"

    def test_status_value(self) -> None:
        assert SessionExportOrderField.STATUS.value == "status"

    def test_created_at_value(self) -> None:
        assert SessionExportOrderField.CREATED_AT.value == "created_at"


class TestProjectExportCSVInput:
    """Tests for ProjectExportCSVInput model."""

    def test_creation_with_all_defaults(self) -> None:
        req = ProjectExportCSVInput()
        assert req.fields is None
        assert req.filter is None
        assert req.order is None
        assert req.encoding == "utf-8"

    def test_creation_with_order(self) -> None:
        order = [
            ProjectExportOrder(field=ProjectExportOrderField.NAME, direction=OrderDirection.DESC)
        ]
        req = ProjectExportCSVInput(order=order)
        assert req.order is not None
        assert req.order[0].field == ProjectExportOrderField.NAME
        assert req.order[0].direction == OrderDirection.DESC

    def test_creation_with_is_active_filter(self) -> None:
        f = ProjectExportFilter(is_active=True)
        req = ProjectExportCSVInput(filter=f)
        assert req.filter is not None
        assert req.filter.is_active is not None
        assert req.filter.is_active is True

    def test_round_trip_serialization(self) -> None:
        req = ProjectExportCSVInput(
            fields=["name", "domain_name"],
            filter=ProjectExportFilter(is_active=False),
            order=[
                ProjectExportOrder(
                    field=ProjectExportOrderField.NAME, direction=OrderDirection.DESC
                )
            ],
        )
        json_data = req.model_dump_json()
        restored = ProjectExportCSVInput.model_validate_json(json_data)
        assert restored.fields == req.fields
        assert restored.filter is not None
        assert restored.filter.is_active is not None
        assert restored.filter.is_active is False
        assert restored.order is not None
        assert restored.order[0].field == ProjectExportOrderField.NAME
        assert restored.order[0].direction == OrderDirection.DESC


class TestProjectExportOrderField:
    """Tests for ProjectExportOrderField StrEnum."""

    def test_name_value(self) -> None:
        assert ProjectExportOrderField.NAME.value == "name"

    def test_domain_name_value(self) -> None:
        assert ProjectExportOrderField.DOMAIN_NAME.value == "domain_name"

    def test_is_active_value(self) -> None:
        assert ProjectExportOrderField.IS_ACTIVE.value == "is_active"

    def test_created_at_value(self) -> None:
        assert ProjectExportOrderField.CREATED_AT.value == "created_at"


class TestAuditLogExportCSVInput:
    """Tests for AuditLogExportCSVInput model."""

    def test_creation_with_all_defaults(self) -> None:
        req = AuditLogExportCSVInput()
        assert req.fields is None
        assert req.filter is None
        assert req.order is None
        assert req.encoding == "utf-8"

    def test_creation_with_status_filter(self) -> None:
        f = AuditLogExportFilter(status=["success"])
        req = AuditLogExportCSVInput(filter=f)
        assert req.filter is not None
        assert req.filter.status == ["success"]

    def test_creation_with_order(self) -> None:
        order = [AuditLogExportOrder(field=AuditLogExportOrderField.CREATED_AT)]
        req = AuditLogExportCSVInput(order=order)
        assert req.order is not None
        assert req.order[0].field == AuditLogExportOrderField.CREATED_AT

    def test_round_trip_serialization(self) -> None:
        req = AuditLogExportCSVInput(
            fields=["entity_type", "operation", "status"],
            filter=AuditLogExportFilter(status=["success", "failure"]),
            order=[
                AuditLogExportOrder(
                    field=AuditLogExportOrderField.CREATED_AT,
                    direction=OrderDirection.DESC,
                )
            ],
        )
        json_data = req.model_dump_json()
        restored = AuditLogExportCSVInput.model_validate_json(json_data)
        assert restored.fields == req.fields
        assert restored.filter is not None
        assert restored.filter.status == ["success", "failure"]
        assert restored.order is not None
        assert restored.order[0].field == AuditLogExportOrderField.CREATED_AT
        assert restored.order[0].direction == OrderDirection.DESC

    def test_model_dump_json_has_snake_case_keys(self) -> None:
        req = AuditLogExportCSVInput()
        data = json.loads(req.model_dump_json())
        assert "fields" in data
        assert "filter" in data
        assert "order" in data
        assert "encoding" in data


class TestAuditLogExportOrderField:
    """Tests for AuditLogExportOrderField StrEnum."""

    def test_entity_type_value(self) -> None:
        assert AuditLogExportOrderField.ENTITY_TYPE.value == "entity_type"

    def test_operation_value(self) -> None:
        assert AuditLogExportOrderField.OPERATION.value == "operation"

    def test_status_value(self) -> None:
        assert AuditLogExportOrderField.STATUS.value == "status"

    def test_created_at_value(self) -> None:
        assert AuditLogExportOrderField.CREATED_AT.value == "created_at"


class TestKeypairExportCSVInput:
    """Tests for KeypairExportCSVInput model."""

    def test_creation_with_all_defaults(self) -> None:
        req = KeypairExportCSVInput()
        assert req.fields is None
        assert req.encoding == "utf-8"

    def test_creation_with_fields(self) -> None:
        req = KeypairExportCSVInput(fields=["access_key", "user_id"])
        assert req.fields == ["access_key", "user_id"]

    def test_creation_with_encoding(self) -> None:
        req = KeypairExportCSVInput(encoding="euc-kr")
        assert req.encoding == "euc-kr"

    def test_round_trip_serialization(self) -> None:
        req = KeypairExportCSVInput(fields=["access_key", "user_id", "is_active"])
        json_data = req.model_dump_json()
        restored = KeypairExportCSVInput.model_validate_json(json_data)
        assert restored.fields == req.fields
        assert restored.encoding == req.encoding
