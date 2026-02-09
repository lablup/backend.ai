"""Tests for entity-level conditions and orders in Fair Share options."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.fair_share.options import (
    DomainFairShareConditions,
    DomainFairShareOrders,
    ProjectFairShareConditions,
    ProjectFairShareOrders,
    UserFairShareConditions,
    UserFairShareOrders,
)


class TestDomainFairShareEntityConditions:
    """Tests for domain entity conditions on DomainFairShareConditions."""

    def test_by_domain_is_active_true(self) -> None:
        condition = DomainFairShareConditions.by_domain_is_active(True)
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_domain_is_active_false(self) -> None:
        condition = DomainFairShareConditions.by_domain_is_active(False)
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)


class TestDomainFairShareEntityOrders:
    """Tests for domain entity orders on DomainFairShareOrders."""

    def test_by_domain_is_active_ascending(self) -> None:
        order = DomainFairShareOrders.by_domain_is_active(ascending=True)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(DomainRow.is_active.asc())

    def test_by_domain_is_active_descending(self) -> None:
        order = DomainFairShareOrders.by_domain_is_active(ascending=False)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(DomainRow.is_active.desc())


class TestProjectFairShareEntityConditions:
    """Tests for project entity conditions on ProjectFairShareConditions."""

    def test_by_project_name_contains(self) -> None:
        condition = ProjectFairShareConditions.by_project_name_contains("test")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_project_name_equals(self) -> None:
        condition = ProjectFairShareConditions.by_project_name_equals("test-project")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_project_name_starts_with(self) -> None:
        condition = ProjectFairShareConditions.by_project_name_starts_with("test")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_project_name_ends_with(self) -> None:
        condition = ProjectFairShareConditions.by_project_name_ends_with("project")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_project_is_active_true(self) -> None:
        condition = ProjectFairShareConditions.by_project_is_active(True)
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_project_is_active_false(self) -> None:
        condition = ProjectFairShareConditions.by_project_is_active(False)
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_project_type_equals(self) -> None:
        condition = ProjectFairShareConditions.by_project_type_equals(ProjectType.GENERAL)
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_project_type_in(self) -> None:
        condition = ProjectFairShareConditions.by_project_type_in([
            ProjectType.GENERAL,
            ProjectType.MODEL_STORE,
        ])
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)


class TestProjectFairShareEntityOrders:
    """Tests for project entity orders on ProjectFairShareOrders."""

    def test_by_project_name_ascending(self) -> None:
        order = ProjectFairShareOrders.by_project_name(ascending=True)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(GroupRow.name.asc())

    def test_by_project_name_descending(self) -> None:
        order = ProjectFairShareOrders.by_project_name(ascending=False)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(GroupRow.name.desc())

    def test_by_project_is_active_ascending(self) -> None:
        order = ProjectFairShareOrders.by_project_is_active(ascending=True)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(GroupRow.is_active.asc())

    def test_by_project_is_active_descending(self) -> None:
        order = ProjectFairShareOrders.by_project_is_active(ascending=False)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(GroupRow.is_active.desc())


class TestUserFairShareEntityConditions:
    """Tests for user entity conditions on UserFairShareConditions."""

    def test_by_user_username_contains(self) -> None:
        condition = UserFairShareConditions.by_user_username_contains("admin")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_username_equals(self) -> None:
        condition = UserFairShareConditions.by_user_username_equals("admin")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_username_starts_with(self) -> None:
        condition = UserFairShareConditions.by_user_username_starts_with("adm")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_username_ends_with(self) -> None:
        condition = UserFairShareConditions.by_user_username_ends_with("min")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_email_contains(self) -> None:
        condition = UserFairShareConditions.by_user_email_contains("@example")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_email_equals(self) -> None:
        condition = UserFairShareConditions.by_user_email_equals("user@example.com")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_email_starts_with(self) -> None:
        condition = UserFairShareConditions.by_user_email_starts_with("user")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_email_ends_with(self) -> None:
        condition = UserFairShareConditions.by_user_email_ends_with(".com")
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_is_active_true(self) -> None:
        condition = UserFairShareConditions.by_user_is_active(True)
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)

    def test_by_user_is_active_false(self) -> None:
        condition = UserFairShareConditions.by_user_is_active(False)
        expr = condition()
        assert isinstance(expr, sa.sql.expression.ColumnElement)


class TestUserFairShareEntityOrders:
    """Tests for user entity orders on UserFairShareOrders."""

    def test_by_user_username_ascending(self) -> None:
        order = UserFairShareOrders.by_user_username(ascending=True)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(UserRow.username.asc())

    def test_by_user_username_descending(self) -> None:
        order = UserFairShareOrders.by_user_username(ascending=False)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(UserRow.username.desc())

    def test_by_user_email_ascending(self) -> None:
        order = UserFairShareOrders.by_user_email(ascending=True)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(UserRow.email.asc())

    def test_by_user_email_descending(self) -> None:
        order = UserFairShareOrders.by_user_email(ascending=False)
        assert isinstance(order, sa.sql.expression.UnaryExpression)
        assert str(order) == str(UserRow.email.desc())
