import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.manager.models.endpoint import (
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.group import resolve_group_name_or_id
from ai.backend.manager.models.image import ImageAlias, ImageIdentifier, ImageRef, ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.services.model_serving.exceptions import (
    EndpointNotFound,
    GenericForbidden,
    InvalidAPIParameters,
    ModelServiceNotFound,
    RouteNotFound,
)
from ai.backend.manager.services.model_serving.types import RequesterCtx
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user_uuid


class ModelServingRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def get_vfolder_by_id(self, vfolder_id: uuid.UUID) -> VFolderRow:
        async with self._db.begin_readonly_session() as db_sess:
            return await VFolderRow.get(db_sess, vfolder_id)

    async def resolve_image(
        self, image_identifiers: list[ImageIdentifier | ImageAlias | ImageRef]
    ) -> ImageRow:
        async with self._db.begin_readonly_session() as db_sess:
            return await ImageRow.resolve(db_sess, image_identifiers)

    async def check_service_name_exists(self, service_name: str) -> bool:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(EndpointRow).where(
                (EndpointRow.lifecycle_stage != EndpointLifecycle.DESTROYED)
                & (EndpointRow.name == service_name)
            )
            result = await db_sess.execute(query)
            return result.scalar() is not None

    async def resolve_group_id(self, domain_name: str, group_name: str) -> uuid.UUID | None:
        async with self._db.begin_session() as db_sess:
            return await resolve_group_name_or_id(
                await db_sess.connection(), domain_name, group_name
            )

    async def create_endpoint(self, endpoint: EndpointRow) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            db_sess.add(endpoint)
            await db_sess.flush()
            return endpoint.id

    async def list_endpoints(
        self, session_owner_id: uuid.UUID, name: str | None = None
    ) -> list[EndpointRow]:
        query_conds = (EndpointRow.session_owner == session_owner_id) & (
            EndpointRow.lifecycle_stage == EndpointLifecycle.CREATED
        )
        if name:
            query_conds &= EndpointRow.name == name

        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(EndpointRow)
                .where(query_conds)
                .options(selectinload(EndpointRow.routings))
            )
            result = await db_sess.execute(query)
            return list(result.scalars().all())

    async def get_endpoint_by_id(
        self, service_id: uuid.UUID, load_routes: bool = False
    ) -> EndpointRow:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                return await EndpointRow.get(db_sess, service_id, load_routes=load_routes)
            except NoResultFound:
                raise ModelServiceNotFound

    async def update_endpoint_to_destroyed(self, service_id: uuid.UUID) -> None:
        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == service_id)
                .values({
                    "lifecycle_stage": EndpointLifecycle.DESTROYED,
                    "destroyed_at": sa.func.now(),
                })
            )
            await db_sess.execute(query)

    async def update_endpoint_to_destroying(self, service_id: uuid.UUID) -> None:
        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == service_id)
                .values({
                    "replicas": 0,
                    "lifecycle_stage": EndpointLifecycle.DESTROYING,
                })
            )
            await db_sess.execute(query)

    async def get_session_by_id(self, session_id: uuid.UUID) -> SessionRow:
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.get_session(db_sess, session_id, None)

    async def delete_failed_routes(self, service_id: uuid.UUID) -> None:
        async with self._db.begin_session() as db_sess:
            query = sa.delete(RoutingRow).where(
                (RoutingRow.endpoint == service_id)
                & (RoutingRow.status == RouteStatus.FAILED_TO_START)
            )
            await db_sess.execute(query)

    async def reset_endpoint_retries(self, endpoint_id: uuid.UUID) -> None:
        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(EndpointRow).values({"retries": 0}).where(EndpointRow.id == endpoint_id)
            )
            await db_sess.execute(query)

    async def get_route_by_id(
        self,
        route_id: uuid.UUID,
        load_endpoint: bool = False,
        load_session: bool = False,
    ) -> RoutingRow:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                return await RoutingRow.get(
                    db_sess, route_id, load_endpoint=load_endpoint, load_session=load_session
                )
            except NoResultFound:
                raise RouteNotFound

    async def update_route_traffic_ratio(self, route_id: uuid.UUID, traffic_ratio: float) -> None:
        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(RoutingRow)
                .where(RoutingRow.id == route_id)
                .values({"traffic_ratio": traffic_ratio})
            )
            await db_sess.execute(query)

    async def get_endpoint_with_routes(self, service_id: uuid.UUID) -> EndpointRow:
        async with self._db.begin_session() as db_sess:
            return await EndpointRow.get(db_sess, service_id, load_routes=True)

    async def update_endpoint_replicas(self, service_id: uuid.UUID, replicas: int) -> None:
        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == service_id)
                .values({"replicas": replicas})
            )
            await db_sess.execute(query)

    async def get_scaling_group_wsproxy_info(self, scaling_group_name: str) -> dict[str, Any]:
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
                .select_from(scaling_groups)
                .where((scaling_groups.c.name == scaling_group_name))
            )
            result = await db_sess.execute(query)
            sgroup = result.first()
            return {
                "wsproxy_addr": sgroup["wsproxy_addr"],
                "wsproxy_api_token": sgroup["wsproxy_api_token"],
            }

    async def create_endpoint_token(self, token_row: EndpointTokenRow) -> EndpointTokenRow:
        async with self._db.begin_session() as db_sess:
            db_sess.add(token_row)
            await db_sess.commit()
            await db_sess.refresh(token_row)
            return token_row

    async def get_endpoint_with_all_relations(
        self,
        endpoint_id: uuid.UUID,
        load_session_owner: bool = False,
        load_model: bool = False,
        load_routes: bool = False,
    ) -> EndpointRow:
        async with self._db.begin_session() as db_sess:
            try:
                return await EndpointRow.get(
                    db_sess,
                    endpoint_id,
                    load_session_owner=load_session_owner,
                    load_model=load_model,
                    load_routes=load_routes,
                )
            except NoResultFound:
                raise EndpointNotFound

    async def commit_endpoint_changes(self, endpoint_row: EndpointRow) -> None:
        async with self._db.begin_session() as db_session:
            db_session.add(endpoint_row)
            await db_session.commit()

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserRow:
        async with self._db.begin_readonly_session() as session:
            query = sa.select(sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)).where(
                UserRow.uuid == user_id
            )
            return (await session.execute(query)).fetchone()

    async def get_session_with_kernels(self, session_id: uuid.UUID) -> SessionRow:
        async with self._db.begin_readonly_session() as db_sess:
            return await SessionRow.get_session(
                db_sess,
                session_id,
                None,
                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
            )

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

    async def get_db_session_for_agent_registry(self):
        # Return a database session for agent registry operations
        # This is temporary until agent registry can be refactored
        return self._db.begin_session()

    async def get_db_session_for_business_logic(self):
        # Return a database session for complex business logic operations
        # This is temporary until business logic can be properly separated
        return self._db.begin_session()
