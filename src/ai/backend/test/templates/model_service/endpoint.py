import asyncio
from abc import abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import Any, override
from uuid import UUID

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.domain import DomainContext
from ai.backend.test.contexts.group import CreatedGroupContext, GroupContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.model_service import (
    CreatedModelServiceEndpointMetaContext,
    ModelServiceContext,
)
from ai.backend.test.contexts.scaling_group import ScalingGroupContext
from ai.backend.test.contexts.session import (
    ClusterContext,
    SessionContext,
)
from ai.backend.test.data.model_service import ModelServiceEndpointMeta
from ai.backend.test.templates.model_service.utils import wait_until_all_inference_sessions_ready
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)
from ai.backend.test.utils.exceptions import DependencyNotSet

_ENDPOINT_CREATION_TIMEOUT = 60


class _BaseEndpointTemplate(WrapperTestTemplate):
    def _build_service_params(self) -> dict[str, Any]:
        session_dep = SessionContext.current()
        scaling_group_dep = ScalingGroupContext.current()
        image_dep = ImageContext.current()
        group_dep = GroupContext.current()
        domain_dep = DomainContext.current()
        model_service_dep = ModelServiceContext.current()
        cluster_dep = ClusterContext.current()

        if not session_dep.resources:
            raise DependencyNotSet("Resources must be defined in the SessionContext.")

        params: dict[str, Any] = {
            "image": image_dep.name,
            "architecture": image_dep.architecture,
            "model_id_or_name": model_service_dep.model_vfolder_name,
            "initial_session_count": model_service_dep.replicas,
            "resources": session_dep.resources,
            "resource_opts": {},
            "domain_name": domain_dep.name,
            "group_name": group_dep.name,
            "scaling_group": scaling_group_dep.name,
            "model_mount_destination": model_service_dep.model_mount_destination,
            "model_definition_path": model_service_dep.model_definition_path,
            "cluster_mode": cluster_dep.cluster_mode,
            "cluster_size": cluster_dep.cluster_size,
            "runtime_variant": model_service_dep.runtime_variant,
            # TODO: Make `envs` required.
            "envs": {
                "TEST_KEY": "test_value",
            },
        }
        params.update(self._extra_service_params())
        return params

    @abstractmethod
    def _extra_service_params(self) -> dict[str, Any]:
        raise NotImplementedError("Subclasses must implement the _extra_service_params method.")

    @override
    @actxmgr
    # TODO: Automatically generate the required model VFolder through the VFolderTemplateWrapper.
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        model_service_dep = ModelServiceContext.current()

        vfolder_func = client_session.VFolder(name=model_service_dep.model_vfolder_name)
        await vfolder_func.update_id_by_name()
        if vfolder_func.id is None:
            raise RuntimeError("Model VFolder id is None.")

        endpoint_id = None
        try:
            response = await client_session.Service.create(
                **self._build_service_params(),
            )

            endpoint_id = UUID(response["endpoint_id"])
            assert response["replicas"] == model_service_dep.replicas, (
                "Replicas count does not match the expected value."
            )

            info = await client_session.Service(endpoint_id).info()
            assert info["service_endpoint"] is None, (
                "Service endpoint should not be initialized yet."
            )
            assert info["runtime_variant"] == model_service_dep.runtime_variant, (
                f"Runtime variant should be '{model_service_dep.runtime_variant}'."
            )
            assert info["desired_session_count"] == model_service_dep.replicas, (
                "Desired session count should match the replicas."
            )
            assert info["model_id"] == str(vfolder_func.id), "Model ID should match the VFolder ID."

            await asyncio.wait_for(
                wait_until_all_inference_sessions_ready(
                    client_session=client_session,
                    endpoint_id=endpoint_id,
                    replicas=model_service_dep.replicas,
                    vfolder_id=vfolder_func.id,
                ),
                timeout=_ENDPOINT_CREATION_TIMEOUT,
            )

            info = await client_session.Service(endpoint_id).info()
            model_service_endpoint = info["service_endpoint"]

            with CreatedModelServiceEndpointMetaContext.with_current(
                ModelServiceEndpointMeta(
                    service_id=endpoint_id,
                    endpoint_url=model_service_endpoint,
                )
            ):
                yield
        finally:
            if endpoint_id:
                response = await client_session.Service(endpoint_id).delete()
                assert response["success"], f"Model Service deletion failed!, response: {response}"


class EndpointTemplate(_BaseEndpointTemplate):
    @property
    def name(self) -> str:
        return "endpoint_template"

    @override
    def _extra_service_params(self) -> dict[str, Any]:
        return {}


class PublicEndpointTemplate(_BaseEndpointTemplate):
    @property
    def name(self) -> str:
        return "public_endpoint_template"

    @override
    def _extra_service_params(self) -> dict[str, Any]:
        return {"expose_to_public": True}


class CustomGroupEndpointTemplate(_BaseEndpointTemplate):
    @property
    def name(self) -> str:
        return "custom_group_endpoint_template"

    @override
    def _extra_service_params(self) -> dict[str, Any]:
        created_group_meta = CreatedGroupContext.current()
        return {"group_name": created_group_meta.group_name}
