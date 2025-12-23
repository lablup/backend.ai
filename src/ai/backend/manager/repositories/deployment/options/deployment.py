"""Query conditions and orders for deployments."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class DeploymentConditions:
    """Query conditions for deployments."""

    @staticmethod
    def by_ids(deployment_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.id.in_(deployment_ids)

        return inner

    @staticmethod
    def by_name_equals(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.name) == value.lower()
            return EndpointRow.name == value

        return inner

    @staticmethod
    def by_name_contains(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.name).contains(value.lower())
            return EndpointRow.name.contains(value)

        return inner

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.project == project_id

        return inner

    @staticmethod
    def by_domain_name_equals(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.domain) == value.lower()
            return EndpointRow.domain == value

        return inner

    @staticmethod
    def by_domain_name_contains(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.domain).contains(value.lower())
            return EndpointRow.domain.contains(value)

        return inner

    @staticmethod
    def by_status_equals(status: ModelDeploymentStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.lifecycle_stage == status

        return inner

    @staticmethod
    def by_status_in(statuses: Collection[ModelDeploymentStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.lifecycle_stage.in_(statuses)

        return inner

    @staticmethod
    def by_open_to_public(value: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.open_to_public == value

        return inner

    @staticmethod
    def by_tag_contains(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.tag).contains(value.lower())
            return EndpointRow.tag.contains(value)

        return inner

    @staticmethod
    def by_tag_equals(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.tag) == value.lower()
            return EndpointRow.tag == value

        return inner

    @staticmethod
    def by_url_contains(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.url).contains(value.lower())
            return EndpointRow.url.contains(value)

        return inner

    @staticmethod
    def by_url_equals(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(EndpointRow.url) == value.lower()
            return EndpointRow.url == value

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointRow.created_at)
                .where(EndpointRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointRow.created_at)
                .where(EndpointRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointRow.created_at > subquery

        return inner


class DeploymentOrders:
    """Query orders for deployments."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.name.asc()
        else:
            return EndpointRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.created_at.asc()
        else:
            return EndpointRow.created_at.desc()
