"""
This script must be executed after updating Backend.AI Core to 25.11.2 and AppProxy to 25.4.1.
Place it under `manager` directory and then run it with manager's python interpreter.
"""

import asyncio
from collections.abc import Coroutine
from http import HTTPStatus
from typing import Optional
from uuid import UUID

import aiohttp
import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from yarl import URL

from ai.backend.common.data.config.types import HealthCheckConfig
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import MODEL_SERVICE_RUNTIME_PROFILES, RuntimeVariant
from ai.backend.logging.types import LogLevel
from ai.backend.manager.cli.context import CLIContext
from ai.backend.manager.config.bootstrap import BootstrapConfig
from ai.backend.manager.config.unified import VolumesConfig
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import VFolderOperationFailed
from ai.backend.manager.models import (
    EndpointLifecycle,
    EndpointRow,
    ScalingGroupRow,
    StorageSessionManager,
    VFolderRow,
)
from ai.backend.manager.models.endpoint import ModelServiceHelper
from ai.backend.manager.models.utils import create_async_engine


async def get_health_check_info(
    storage_manager: StorageSessionManager, endpoint: EndpointRow, model: VFolderRow
) -> Optional[HealthCheckConfig]:
    if _path := MODEL_SERVICE_RUNTIME_PROFILES[endpoint.runtime_variant].health_check_endpoint:
        return HealthCheckConfig(path=_path)
    elif endpoint.runtime_variant == RuntimeVariant.CUSTOM:
        model_definition_path = await ModelServiceHelper.validate_model_definition_file_exists(
            storage_manager,
            model.host,
            model.vfid,
            endpoint.model_definition_path,
        )
        try:
            model_definition = await ModelServiceHelper.validate_model_definition(
                storage_manager,
                model.host,
                model.vfid,
                model_definition_path,
            )
        except InvalidAPIParameters:
            return None
        for model_info in model_definition["models"]:
            if health_check_info := (model_info.get("service") or {}).get("health_check"):
                return HealthCheckConfig(
                    path=health_check_info["path"],
                    interval=health_check_info["interval"],
                    max_retries=health_check_info["max_retries"],
                    max_wait_time=health_check_info["max_wait_time"],
                    expected_status_code=health_check_info["expected_status_code"],
                )
    return None


async def update_appproxy_endpoint_entity(
    addr: str,
    token: str,
    endpoint: UUID,
    health_check_config: HealthCheckConfig,
) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.put(
            f"{addr}/v2/endpoints/{endpoint}/health-check",
            json={
                "health_check": health_check_config.model_dump(mode="json")
            },  # TODO: support for multiple inference apps
            headers={
                "X-BackendAI-Token": token,
            },
        ) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                if e.status == HTTPStatus.NOT_FOUND:
                    pass


async def main(get_bootstrap_config_coro: Coroutine[None, None, BootstrapConfig]) -> None:
    config: BootstrapConfig = await get_bootstrap_config_coro
    etcd = AsyncEtcd.initialize(config.etcd.to_dataclass())
    raw_volumes_config = await etcd.get_prefix("volumes")
    storage_manager = StorageSessionManager(VolumesConfig(**raw_volumes_config))

    db_username = config.db.user
    db_password = config.db.password
    db_addr = config.db.addr
    db_name = config.db.name
    db_url = URL(f"postgresql+asyncpg://{db_addr.host}/{db_name}")
    db_url = db_url.with_port(db_addr.port)
    db_url = db_url.with_user(db_username)
    if db_password is not None:
        db_url = db_url.with_password(db_password)
    engine = create_async_engine(str(db_url))

    appproxy_info: dict[str, ScalingGroupRow] = {}

    async with engine.begin_session() as sess:
        query = (
            sa.select(EndpointRow)
            .where(EndpointRow.lifecycle_stage == EndpointLifecycle.CREATED)
            .options(selectinload(EndpointRow.model_row))
        )
        result = await sess.execute(query)
        rows: list[EndpointRow] = result.scalars().all()
        for endpoint in rows:
            try:
                health_check_info = await get_health_check_info(
                    storage_manager,
                    endpoint,
                    endpoint.model_row,
                )
                print(endpoint.name, ":", health_check_info)
            except VFolderOperationFailed:
                continue
            if not health_check_info:
                continue

            if endpoint.resource_group not in appproxy_info:
                query = sa.select(ScalingGroupRow).where(
                    ScalingGroupRow.name == endpoint.resource_group
                )
                result = await sess.execute(query)
                sgroup = result.scalar()
                appproxy_info[endpoint.resource_group] = sgroup
            else:
                sgroup = appproxy_info[endpoint.resource_group]

            await update_appproxy_endpoint_entity(
                sgroup.wsproxy_addr, sgroup.wsproxy_api_token, endpoint.id, health_check_info
            )
            print(f"Inserted health check config of endpoint {endpoint.id} to AppProxy")


if __name__ == "__main__":
    cli_ctx = CLIContext(LogLevel.INFO)
    config = cli_ctx.get_bootstrap_config()

    asyncio.run(main(config))
