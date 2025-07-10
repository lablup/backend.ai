import decimal
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.models.endpoint import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.model_serving.exceptions import (
    EndpointAutoScalingRuleNotFound,
    EndpointNotFound,
    GenericForbidden,
    InvalidAPIParameters,
    ModelServiceNotFound,
)
from ai.backend.manager.services.model_serving.types import RequesterCtx
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user_uuid


class AutoScalingRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def get_endpoint_by_id(
        self, service_id: uuid.UUID, load_routes: bool = False
    ) -> EndpointRow:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                return await EndpointRow.get(db_sess, service_id, load_routes=load_routes)
            except NoResultFound:
                raise ModelServiceNotFound

    async def update_endpoint_replicas(self, service_id: uuid.UUID, replicas: int) -> None:
        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == service_id)
                .values({"replicas": replicas})
            )
            await db_sess.execute(query)

    async def get_endpoint_for_auto_scaling_rule(self, endpoint_id: uuid.UUID) -> EndpointRow:
        async with self._db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointRow.get(db_session, endpoint_id)
                if row.lifecycle_stage in EndpointLifecycle.inactive_states():
                    raise EndpointNotFound
                return row
            except NoResultFound:
                raise EndpointNotFound

    async def get_auto_scaling_rule_by_id(
        self, rule_id: uuid.UUID, load_endpoint: bool = False
    ) -> EndpointAutoScalingRuleRow:
        async with self._db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointAutoScalingRuleRow.get(
                    db_session, rule_id, load_endpoint=load_endpoint
                )
                if (
                    load_endpoint
                    and row.endpoint_row.lifecycle_stage in EndpointLifecycle.inactive_states()
                ):
                    raise EndpointAutoScalingRuleNotFound
                return row
            except NoResultFound:
                raise EndpointAutoScalingRuleNotFound

    async def delete_auto_scaling_rule(self, rule: EndpointAutoScalingRuleRow) -> None:
        async with self._db.begin_session(commit_on_end=True) as db_session:
            await db_session.delete(rule)

    async def verify_user_access_scopes(
        self, requester_ctx: RequesterCtx, owner_uuid: uuid.UUID
    ) -> None:
        if requester_ctx.is_authorized is False:
            raise GenericForbidden("Only authorized requests may have access key scopes.")
        if owner_uuid is None or owner_uuid == requester_ctx.user_id:
            return
        async with self._db.begin_readonly() as conn:
            try:
                await check_if_requester_is_eligible_to_act_as_target_user_uuid(
                    conn,
                    requester_ctx.user_role,
                    requester_ctx.domain_name,
                    owner_uuid,
                )
                return
            except ValueError as e:
                raise InvalidAPIParameters(str(e))
            except RuntimeError as e:
                raise GenericForbidden(str(e))

    async def create_auto_scaling_rule(
        self,
        endpoint_row: EndpointRow,
        metric_source: str,
        metric_name: str,
        threshold: decimal.Decimal,
        comparator: str,
        step_size: int,
        cooldown_seconds: int | None = None,
        min_replicas: int | None = None,
        max_replicas: int | None = None,
    ) -> EndpointAutoScalingRuleRow:
        async with self._db.begin_session(commit_on_end=True) as db_session:
            created_rule = await endpoint_row.create_auto_scaling_rule(
                db_session,
                AutoScalingMetricSource(metric_source),
                metric_name,
                threshold,
                AutoScalingMetricComparator(comparator),
                step_size,
                cooldown_seconds=cooldown_seconds or 0,
                min_replicas=min_replicas or 1,
                max_replicas=max_replicas or 10,
            )
            return created_rule

    async def update_auto_scaling_rule(
        self, rule_row: EndpointAutoScalingRuleRow, fields_to_update: dict[str, Any]
    ) -> EndpointAutoScalingRuleRow:
        async with self._db.begin_session(commit_on_end=True) as db_session:
            for key, value in fields_to_update.items():
                setattr(rule_row, key, value)
            await db_session.commit()
            return rule_row
