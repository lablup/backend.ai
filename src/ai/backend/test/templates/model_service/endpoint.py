import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override
from uuid import UUID

import aiohttp

from ai.backend.client.output.fields import session_node_fields
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.domain import DomainContext
from ai.backend.test.contexts.group import GroupContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.model_service import ModelServiceContext
from ai.backend.test.contexts.scaling_group import ScalingGroupContext
from ai.backend.test.contexts.session import (
    ClusterContext,
    SessionContext,
)
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)
from ai.backend.test.utils.exceptions import DependencyNotSet

_ENDPOINT_CREATION_TIMEOUT = 30
_ENDPOINT_HEALTH_CHECK_TIMEOUT = 10


class EndpointTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "endpoint"

    @override
    @actxmgr
    # TODO: Automatically generate the required model VFolder through the VFolderTemplateWrapper.
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        session_dep = SessionContext.current()
        scaling_group_dep = ScalingGroupContext.current()
        image_dep = ImageContext.current()
        group_dep = GroupContext.current()
        domain_dep = DomainContext.current()
        model_service_dep = ModelServiceContext.current()
        cluster_dep = ClusterContext.current()

        if not session_dep.resources:
            raise DependencyNotSet("Resources must be defined in the SessionContext.")

        vfolder_func = client_session.VFolder(name=model_service_dep.model_vfolder_name)
        await vfolder_func.update_id_by_name()

        endpoint_id = None
        try:
            response = await client_session.Service.create(
                image=image_dep.name,
                architecture=image_dep.architecture,
                model_id_or_name=model_service_dep.model_vfolder_name,
                initial_session_count=model_service_dep.replicas,
                resources=session_dep.resources,
                resource_opts={},
                domain_name=domain_dep.name,
                group_name=group_dep.name,
                scaling_group=scaling_group_dep.name,
                model_mount_destination=model_service_dep.model_mount_destination,
                model_definition_path=model_service_dep.model_definition_path,
                cluster_mode=cluster_dep.cluster_mode,
                cluster_size=cluster_dep.cluster_size,
                # TODO: Make `envs` required.
                envs={},
            )

            endpoint_id = response["endpoint_id"]
            assert response["replicas"] == model_service_dep.replicas, (
                "Replicas count does not match the expected value."
            )
            assert not response["is_public"], "Service should not be public by default."

            info = await client_session.Service(endpoint_id).info()
            assert info["service_endpoint"] is None, "Service endpoint should not be given yet."
            assert info["runtime_variant"] == "custom", (
                "Default runtime variant should be 'custom'."
            )
            assert info["desired_session_count"] == model_service_dep.replicas, (
                "Desired session count should match the replicas."
            )
            assert info["model_id"] == str(vfolder_func.id), "Model ID should match the VFolder ID."

            async def _wait_until_all_inference_sessions_ready() -> None:
                while True:
                    result = await client_session.Service(endpoint_id).info()
                    active_routes = result["active_routes"]
                    session_ids = [route["session_id"] for route in active_routes]

                    ready_session_cnt = 0
                    for session_id in session_ids:
                        session_info = await client_session.ComputeSession.from_session_id(
                            UUID(session_id)
                        ).detail([
                            session_node_fields["type"],
                            session_node_fields["status"],
                            session_node_fields["vfolder_mounts"],
                        ])

                        assert session_info["type"] == "inference", (
                            f"Session type should be 'inference'., Actual type: {session_info['type']}, session_id: {session_id}"
                        )
                        assert session_info["vfolder_mounts"] == [str(vfolder_func.id)], (
                            f"Model vfolder should be mounted into the inference session., Actual mounted vfolder: {session_info['vfolder_mounts']}, session_id: {session_id}"
                        )
                        if session_info["status"] == "RUNNING":
                            ready_session_cnt += 1

                    if ready_session_cnt >= model_service_dep.replicas:
                        break

                    await asyncio.sleep(1)

            await asyncio.wait_for(
                _wait_until_all_inference_sessions_ready(), timeout=_ENDPOINT_CREATION_TIMEOUT
            )

            info = await client_session.Service(endpoint_id).info()
            assert info["service_endpoint"] is not None, "Service endpoint should be initialized."

            async with aiohttp.ClientSession() as http_sess:
                resp = await asyncio.wait_for(
                    http_sess.get(info["service_endpoint"]), timeout=_ENDPOINT_HEALTH_CHECK_TIMEOUT
                )
                assert resp.status // 100 == 2, (
                    f"Service endpoint health check failed with status: {resp.status}"
                )
            yield
        finally:
            if endpoint_id:
                response = await client_session.Service(endpoint_id).delete()
                assert response["success"], f"Model Service deletion failed!, response: {response}"
