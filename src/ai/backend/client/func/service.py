import textwrap
from typing import Any, Literal, Mapping, Optional, Sequence
from uuid import UUID

from faker import Faker

from ai.backend.client.exceptions import BackendClientError
from ai.backend.client.output.fields import service_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.client.pagination import fetch_paginated_result
from ai.backend.client.request import Request
from ai.backend.client.session import api_session
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH

from .base import BaseFunction, api_function

__all__ = ("Service",)

_default_fields: Sequence[FieldSpec] = (
    service_fields["endpoint_id"],
    service_fields["name"],
    service_fields["image"],
    service_fields["desired_session_count"],
    service_fields["routings"],
    service_fields["session_owner"],
    service_fields["open_to_public"],
)


class Service(BaseFunction):
    id: UUID

    @api_function
    @classmethod
    async def list(cls, name: Optional[str] = None):
        """ """
        params = {}
        if name:
            params["name"] = name
        rqst = Request("GET", "/services", params=params)
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        *,
        fields: Sequence[FieldSpec] = _default_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult:
        """ """
        return await fetch_paginated_result(
            "endpoint_list",
            {
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_size=page_size,
            page_offset=page_offset,
        )

    @api_function
    @classmethod
    async def detail(
        cls,
        service_id: str,
        fields: Sequence[FieldSpec] = _default_fields,
    ) -> Sequence[dict]:
        query = textwrap.dedent(
            """\
            query($endpoint_id: UUID!) {
                endpoint(endpoint_id: $endpoint_id) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"endpoint_id": service_id}
        data = await api_session.get().Admin._query(query, variables)
        return data["endpoint"]

    @api_function
    @classmethod
    async def create(
        cls,
        image: str,
        model_id_or_name: str,
        initial_session_count: int,
        *,
        extra_mounts: Sequence[str] = [],
        extra_mount_map: Mapping[str, str] = {},
        extra_mount_options: Mapping[str, Mapping[str, str]] = {},
        service_name: Optional[str] = None,
        model_version: Optional[str] = None,
        dependencies: Optional[Sequence[str]] = None,
        model_mount_destination: Optional[str] = None,
        envs: Optional[Mapping[str, str]] = None,
        startup_command: Optional[str] = None,
        resources: Optional[Mapping[str, str | int]] = None,
        resource_opts: Optional[Mapping[str, str | int]] = None,
        cluster_size: int = 1,
        cluster_mode: Literal["single-node", "multi-node"] = "single-node",
        domain_name: Optional[str] = None,
        group_name: Optional[str] = None,
        bootstrap_script: Optional[str] = None,
        tag: Optional[str] = None,
        architecture: Optional[str] = DEFAULT_IMAGE_ARCH,
        scaling_group: Optional[str] = None,
        owner_access_key: Optional[str] = None,
        model_definition_path: Optional[str] = None,
        expose_to_public=False,
    ) -> Any:
        """
        Creates an inference service.

        :param image: The image name and tag for the infernence session.
            Example: ``python:3.6-ubuntu``.
            Check out the full list of available images in your server using (TODO:
            new API).
        :param service_name: A client-side (user-defined) identifier to distinguish the session among currently
            running sessions.
            It may be used to seamlessly reuse the session already created.
        :param initial_session_count: Number of sessions to be started along with
            service initiation.
        :param mounts: The ID of model type vFolder which contains model files required
            to start inference session.
        :param model_mount_destination: Path inside the container to mount model vFolder,
            defaults to /models
        :param envs: The environment variables which always bypasses the jail policy.
        :param resources: The resource specification. (TODO: details)
        :param cluster_size: The number of containers in this compute session.
            Must be at least 1.
        :param cluster_mode: Set the clustering mode whether to use distributed
            nodes or a single node to spawn multiple containers for the new session.
        :param tag: An optional string to annotate extra information.
        :param owner: An optional access key that owns the created session. (Only
            available to administrators)
        :param model_definition_path: Relative path to model definition file. Defaults to `model-definition.yaml`.
        :param expose_to_public: Visibility of API Endpoint which serves inference workload.
            If set to true, no authentication will be required to access the endpoint.

        :returns: The :class:`ComputeSession` instance.
        """
        if service_name is None:
            faker = Faker()
            service_name = f"bai-serve-{faker.user_name()}"

        if extra_mounts:
            vfolder_id_to_name: dict[UUID, str] = {}
            vfolder_name_to_id: dict[str, UUID] = {}

            rqst = Request("GET", "/folders")
            async with rqst.fetch() as resp:
                body = await resp.json()
                for folder_info in body:
                    vfolder_id_to_name[UUID(folder_info["id"])] = folder_info["name"]
                    vfolder_name_to_id[folder_info["name"]] = UUID(folder_info["id"])

            extra_mount_body = {}

            for mount in extra_mounts:
                try:
                    vfolder_id = UUID(mount)
                    if vfolder_id not in vfolder_id_to_name:
                        raise BackendClientError(f"VFolder (id: {vfolder_id}) not found")
                except ValueError:
                    if mount not in vfolder_name_to_id:
                        raise BackendClientError(f"VFolder (name: {vfolder_id}) not found")
                    vfolder_id = vfolder_name_to_id[mount]
                extra_mount_body[str(vfolder_id)] = {
                    "mount_destination": extra_mount_map.get(mount),
                    "type": extra_mount_options.get(mount, {}).get("type"),
                }
        model_config = {
            "model": model_id_or_name,
            "model_mount_destination": model_mount_destination,
            "extra_mounts": extra_mount_body,
            "environ": envs,
            "scaling_group": scaling_group,
            "resources": resources,
            "resource_opts": resource_opts,
            "model_definition_path": model_definition_path,
        }
        if model_version:
            model_config["model_version"] = model_version
        rqst = Request("POST", "/services")
        rqst.set_json({
            "name": service_name,
            "desired_session_count": initial_session_count,
            "image": image,
            "arch": architecture,
            "group": group_name,
            "domain": domain_name,
            "cluster_size": cluster_size,
            "cluster_mode": cluster_mode,
            "tag": tag,
            "startup_command": startup_command,
            "bootstrap_script": bootstrap_script,
            "owner_access_key": owner_access_key,
            "open_to_public": expose_to_public,
            "config": model_config,
        })
        async with rqst.fetch() as resp:
            body = await resp.json()
            return {
                "endpoint_id": body["endpoint_id"],
                "name": service_name,
                "desired_session_count": initial_session_count,
                "active_route_count": 0,
                "service_endpoint": None,
                "is_public": expose_to_public,
            }

    @api_function
    @classmethod
    async def try_start(
        cls,
        image: str,
        model_id_or_name: str,
        *,
        service_name: Optional[str] = None,
        model_version: Optional[str] = None,
        dependencies: Optional[Sequence[str]] = None,
        model_mount_destination: Optional[str] = None,
        envs: Optional[Mapping[str, str]] = None,
        startup_command: Optional[str] = None,
        resources: Optional[Mapping[str, str | int]] = None,
        resource_opts: Optional[Mapping[str, str | int]] = None,
        cluster_size: int = 1,
        cluster_mode: Literal["single-node", "multi-node"] = "single-node",
        domain_name: Optional[str] = None,
        group_name: Optional[str] = None,
        bootstrap_script: Optional[str] = None,
        tag: Optional[str] = None,
        architecture: Optional[str] = DEFAULT_IMAGE_ARCH,
        scaling_group: Optional[str] = None,
        owner_access_key: Optional[str] = None,
        expose_to_public=False,
    ) -> Any:
        """
        Tries to start an inference session and terminates immediately.

        :param image: The image name and tag for the infernence session.
            Example: ``python:3.6-ubuntu``.
            Check out the full list of available images in your server using (TODO:
            new API).
        :param service_name: A client-side (user-defined) identifier to distinguish the session among currently
            running sessions.
            It may be used to seamlessly reuse the session already created.
        :param mounts: The ID of model type vFolder which contains model files required
            to start inference session.
        :param model_mount_destination: Path inside the container to mount model vFolder,
            defaults to /models
        :param envs: The environment variables which always bypasses the jail policy.
        :param resources: The resource specification. (TODO: details)
        :param cluster_size: The number of containers in this compute session.
            Must be at least 1.
        :param cluster_mode: Set the clustering mode whether to use distributed
            nodes or a single node to spawn multiple containers for the new session.
        :param tag: An optional string to annotate extra information.
        :param owner: An optional access key that owns the created session. (Only
            available to administrators)
        :param expose_to_public: Visibility of API Endpoint which serves inference workload.
            If set to true, no authentication will be required to access the endpoint.

        :returns: The :class:`ComputeSession` instance.
        """
        if service_name is None:
            faker = Faker()
            service_name = f"bai-serve-{faker.user_name()}"

        rqst = Request("POST", "/services/_/try")
        rqst.set_json({
            "name": service_name,
            "desired_session_count": 1,
            "image": image,
            "arch": architecture,
            "group": group_name,
            "domain": domain_name,
            "cluster_size": cluster_size,
            "cluster_mode": cluster_mode,
            "tag": tag,
            "startup_command": startup_command,
            "bootstrap_script": bootstrap_script,
            "owner_access_key": owner_access_key,
            "open_to_public": expose_to_public,
            "config": {
                "model": model_id_or_name,
                "model_version": model_version,
                "model_mount_destination": model_mount_destination,
                "environ": envs,
                "scaling_group": scaling_group,
                "resources": resources,
                "resource_opts": resource_opts,
            },
        })
        async with rqst.fetch() as resp:
            body = await resp.json()
            return {
                "task_id": body["task_id"],
                "name": service_name,
            }

    def __init__(self, id: str | UUID) -> None:
        super().__init__()
        self.id = id if isinstance(id, UUID) else UUID(id)

    @api_function
    async def info(self):
        rqst = Request("GET", f"/services/{self.id}")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def delete(self):
        rqst = Request("DELETE", f"/services/{self.id}")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def sync(self):
        rqst = Request("POST", f"/services/{self.id}/sync")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def scale(self, to: int):
        rqst = Request("POST", f"/services/{self.id}/scale")
        rqst.set_json({"to": to})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def generate_api_token(self, duration: str):
        rqst = Request("POST", f"/services/{self.id}/token")
        rqst.set_json({"duration": duration})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def update_traffic_ratio(self, target_route_id: UUID, new_ratio: float):
        rqst = Request("PUT", f"/services/{self.id}/routings/{target_route_id}")
        rqst.set_json({"traffic_ratio": new_ratio})
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def downscale_single_route(self, target_route_id: UUID):
        rqst = Request("DELETE", f"/services/{self.id}/routings/{target_route_id}")
        async with rqst.fetch() as resp:
            return await resp.json()
