"""Query conditions for endpoint models."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.repositories.base import QueryCondition


class DeploymentConditions:
    """Query conditions for deployments."""

    @staticmethod
    def by_ids(deployment_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.id.in_(deployment_ids)

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(EndpointRow.name) == spec.value.lower()
            else:
                condition = EndpointRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.name.ilike(f"%{spec.value}%")
            else:
                condition = EndpointRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.name.ilike(f"{spec.value}%")
            else:
                condition = EndpointRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.name.ilike(f"%{spec.value}")
            else:
                condition = EndpointRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.project == project_id

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(EndpointRow.domain) == spec.value.lower()
            else:
                condition = EndpointRow.domain == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.domain.ilike(f"%{spec.value}%")
            else:
                condition = EndpointRow.domain.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.domain.ilike(f"{spec.value}%")
            else:
                condition = EndpointRow.domain.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.domain.ilike(f"%{spec.value}")
            else:
                condition = EndpointRow.domain.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

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
    def by_lifecycle_stages(statuses: Collection[EndpointLifecycle]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.lifecycle_stage.in_(statuses)

        return inner

    @staticmethod
    def by_open_to_public(value: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointRow.open_to_public == value

        return inner

    @staticmethod
    def by_tag_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.tag.ilike(f"%{spec.value}%")
            else:
                condition = EndpointRow.tag.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_tag_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(EndpointRow.tag) == spec.value.lower()
            else:
                condition = EndpointRow.tag == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_tag_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.tag.ilike(f"{spec.value}%")
            else:
                condition = EndpointRow.tag.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_tag_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.tag.ilike(f"%{spec.value}")
            else:
                condition = EndpointRow.tag.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_url_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.url.ilike(f"%{spec.value}%")
            else:
                condition = EndpointRow.url.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_url_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(EndpointRow.url) == spec.value.lower()
            else:
                condition = EndpointRow.url == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_url_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.url.ilike(f"{spec.value}%")
            else:
                condition = EndpointRow.url.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_url_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = EndpointRow.url.ilike(f"%{spec.value}")
            else:
                condition = EndpointRow.url.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

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


class AccessTokenConditions:
    """Query conditions for access tokens."""

    @staticmethod
    def by_ids(token_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.id.in_(token_ids)

        return inner

    @staticmethod
    def by_endpoint_id(endpoint_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.endpoint == endpoint_id

        return inner

    # Token string conditions
    @staticmethod
    def by_token_equals(value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.token == value

        return inner

    @staticmethod
    def by_token_contains(value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.token.contains(value)

        return inner

    # expires_at datetime conditions
    @staticmethod
    def by_expires_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.expires_at < dt

        return inner

    @staticmethod
    def by_expires_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.expires_at > dt

        return inner

    @staticmethod
    def by_expires_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.expires_at == dt

        return inner

    # created_at datetime conditions
    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.created_at == dt

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointTokenRow.created_at)
                .where(EndpointTokenRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointTokenRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointTokenRow.created_at)
                .where(EndpointTokenRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointTokenRow.created_at > subquery

        return inner


class AutoScalingRuleConditions:
    """Query conditions for auto-scaling rules."""

    @staticmethod
    def by_ids(rule_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.id.in_(rule_ids)

        return inner

    @staticmethod
    def by_endpoint_id(endpoint_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.endpoint == endpoint_id

        return inner

    @staticmethod
    def by_deployment_id(deployment_id: uuid.UUID) -> QueryCondition:
        """Alias for by_endpoint_id for consistency with deployment naming."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.endpoint == deployment_id

        return inner

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.created_at == dt

        return inner

    @staticmethod
    def by_last_triggered_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.last_triggered_at < dt

        return inner

    @staticmethod
    def by_last_triggered_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.last_triggered_at > dt

        return inner

    @staticmethod
    def by_last_triggered_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.last_triggered_at == dt

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointAutoScalingRuleRow.created_at)
                .where(EndpointAutoScalingRuleRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointAutoScalingRuleRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointAutoScalingRuleRow.created_at)
                .where(EndpointAutoScalingRuleRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointAutoScalingRuleRow.created_at > subquery

        return inner
