"""Query conditions and orders for deployments."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.deployment.types import EndpointLifecycle
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
        """Filter by tag key or value containing the specified string.

        Searches in both keys and values of the JSON dict.
        For key-only search, use "key:" format (e.g., "project:").
        For key-value search, use "key=value" format (e.g., "project=ai").
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            # Parse spec.value to determine search intent
            if "=" in spec.value:
                # key=value format: exact key-value match
                key, value = spec.value.split("=", 1)
                json_tag = sa.cast(EndpointRow.tag, JSONB)
                if spec.case_insensitive:
                    condition = sa.func.lower(json_tag[key].astext) == value.lower()
                else:
                    condition = json_tag[key].astext == value
            elif spec.value.endswith(":"):
                # key: format: check key existence
                key = spec.value[:-1]
                json_tag = sa.cast(EndpointRow.tag, JSONB)
                condition = json_tag.has_key(key)
            else:
                # Default: search in both keys and values using text cast
                json_text = sa.cast(EndpointRow.tag, sa.Text)
                if spec.case_insensitive:
                    condition = json_text.ilike(f'%"{spec.value}"%')
                else:
                    condition = json_text.like(f'%"{spec.value}"%')
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_tag_equals(spec: StringMatchSpec) -> QueryCondition:
        """Filter by exact tag key-value match.

        Expects "key=value" format. For key existence check, use by_tag_contains with "key:" format.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if "=" not in spec.value:
                raise ValueError(f"by_tag_equals expects 'key=value' format, got: '{spec.value}'")
            key, value = spec.value.split("=", 1)
            json_tag = sa.cast(EndpointRow.tag, JSONB)
            if spec.case_insensitive:
                condition = sa.func.lower(json_tag[key].astext) == value.lower()
            else:
                condition = json_tag[key].astext == value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_tag_starts_with(spec: StringMatchSpec) -> QueryCondition:
        """Filter by tag value starting with the specified string.

        Expects "key=prefix" format. Matches tags where tag[key] starts with prefix.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if "=" not in spec.value:
                raise ValueError(
                    f"by_tag_starts_with expects 'key=prefix' format, got: '{spec.value}'"
                )
            key, prefix = spec.value.split("=", 1)
            json_tag = sa.cast(EndpointRow.tag, JSONB)
            if spec.case_insensitive:
                condition = sa.func.lower(json_tag[key].astext).like(f"{prefix.lower()}%")
            else:
                condition = json_tag[key].astext.like(f"{prefix}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_tag_ends_with(spec: StringMatchSpec) -> QueryCondition:
        """Filter by tag value ending with the specified string.

        Expects "key=suffix" format. Matches tags where tag[key] ends with suffix.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if "=" not in spec.value:
                raise ValueError(
                    f"by_tag_ends_with expects 'key=suffix' format, got: '{spec.value}'"
                )
            key, suffix = spec.value.split("=", 1)
            json_tag = sa.cast(EndpointRow.tag, JSONB)
            if spec.case_insensitive:
                condition = sa.func.lower(json_tag[key].astext).like(f"%{suffix.lower()}")
            else:
                condition = json_tag[key].astext.like(f"%{suffix}")
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


class DeploymentOrders:
    """Query orders for deployments."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.name.asc()
        return EndpointRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.created_at.asc()
        return EndpointRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.updated_at.asc()
        return EndpointRow.updated_at.desc()
