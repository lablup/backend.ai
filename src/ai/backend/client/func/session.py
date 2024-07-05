from __future__ import annotations

import json
import os
import secrets
import tarfile
import tempfile
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    cast,
)
from uuid import UUID

import aiohttp
from aiohttp import hdrs
from faker import Faker
from tqdm import tqdm

from ai.backend.client.output.fields import session_fields
from ai.backend.client.output.types import FieldSpec, PaginatedResult
from ai.backend.common.arch import DEFAULT_IMAGE_ARCH
from ai.backend.common.types import ClusterMode, SessionTypes

from ...cli.types import Undefined, undefined
from ..compat import current_loop
from ..config import DEFAULT_CHUNK_SIZE
from ..exceptions import BackendClientError
from ..pagination import fetch_paginated_result
from ..request import (
    AttachedFile,
    Request,
    SSEContextManager,
    WebSocketContextManager,
    WebSocketResponse,
)
from ..session import api_session
from ..utils import ProgressReportingReader
from ..versioning import get_id_or_name, get_naming
from .base import BaseFunction, api_function

__all__ = ("ComputeSession", "InferenceSession")

_default_list_fields = (
    session_fields["session_id"],
    session_fields["image"],
    session_fields["type"],
    session_fields["status"],
    session_fields["status_info"],
    session_fields["status_changed"],
    session_fields["result"],
    session_fields["abusing_reports"],
)


def drop(d: Mapping[str, Any], value_to_drop: Any) -> Mapping[str, Any]:
    modified: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, Mapping) or isinstance(v, dict):
            modified[k] = drop(v, value_to_drop)
        elif v != value_to_drop:
            modified[k] = v
    return modified


class ComputeSession(BaseFunction):
    """
    Provides various interactions with compute sessions in Backend.AI.

    The term 'kernel' is now deprecated and we prefer 'compute sessions'.
    However, for historical reasons and to avoid confusion with client sessions, we
    keep the backward compatibility with the naming of this API function class.

    For multi-container sessions, all methods take effects to the master container
    only, except :func:`~ComputeSession.destroy` and :func:`~ComputeSession.restart` methods.
    So it is the user's responsibility to distribute uploaded files to multiple
    containers using explicit copies or virtual folders which are commonly mounted to
    all containers belonging to the same compute session.
    """

    id: Optional[UUID]
    name: Optional[str]
    owner_access_key: Optional[str]
    created: bool
    status: str
    service_ports: List[str]
    domain: str
    group: str

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str = None,
        access_key: str = None,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of sessions.

        :param status: Fetches sessions in a specific status
                       (PENDING, SCHEDULED, PULLING, PREPARING,
                        RUNNING, RESTARTING, RUNNING_DEGRADED,
                        TERMINATING, TERMINATED, ERROR, CANCELLED)
        :param fields: Additional per-session query fields to fetch.
        """
        return await fetch_paginated_result(
            "compute_session_list",
            {
                "status": (status, "String"),
                "access_key": (access_key, "String"),
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def hello(cls) -> str:
        rqst = Request("GET", "/")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_task_logs(
        cls,
        task_id: str,
        *,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "GET",
            f"/{prefix}/_/logs",
            params={
                "taskId": task_id,
            },
        )
        async with rqst.fetch() as resp:
            while True:
                chunk = await resp.raw_response.content.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @api_function
    @classmethod
    async def get_or_create(
        cls,
        image: str,
        *,
        name: str = None,
        type_: str = SessionTypes.INTERACTIVE.value,
        starts_at: str = None,
        enqueue_only: bool = False,
        max_wait: int = 0,
        no_reuse: bool = False,
        dependencies: Sequence[str] = None,
        callback_url: Optional[str] = None,
        mounts: List[str] = None,
        mount_map: Mapping[str, str] = None,
        mount_options: Optional[Mapping[str, Mapping[str, str]]] = None,
        envs: Mapping[str, str] = None,
        startup_command: str = None,
        resources: Mapping[str, str | int] = None,
        resource_opts: Mapping[str, str | int] = None,
        cluster_size: int = 1,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        domain_name: str = None,
        group_name: str = None,
        bootstrap_script: str = None,
        tag: str = None,
        architecture: str = DEFAULT_IMAGE_ARCH,
        scaling_group: str = None,
        owner_access_key: str = None,
        preopen_ports: List[int] = None,
        assign_agent: List[str] = None,
    ) -> ComputeSession:
        """
        Get-or-creates a compute session.
        If *name* is ``None``, it creates a new compute session as long as
        the server has enough resources and your API key has remaining quota.
        If *name* is a valid string and there is an existing compute session
        with the same token and the same *image*, then it returns the :class:`ComputeSession`
        instance representing the existing session.

        :param image: The image name and tag for the compute session.
            Example: ``python:3.6-ubuntu``.
            Check out the full list of available images in your server using (TODO:
            new API).
        :param name: A client-side (user-defined) identifier to distinguish the session among currently
            running sessions.
            It may be used to seamlessly reuse the session already created.

            .. versionchanged:: 19.12.0

               Renamed from ``clientSessionToken``.
        :param type_: Either ``"interactive"`` (default) or ``"batch"``.

            .. versionadded:: 19.09.0
        :param enqueue_only: Just enqueue the session creation request and return immediately,
            without waiting for its startup. (default: ``false`` to preserve the legacy
            behavior)

            .. versionadded:: 19.09.0
        :param max_wait: The time to wait for session startup. If the cluster resource
            is being fully utilized, this waiting time can be arbitrarily long due to
            job queueing.  If the timeout reaches, the returned *status* field becomes
            ``"TIMEOUT"``.  Still in this case, the session may start in the future.

            .. versionadded:: 19.09.0
        :param no_reuse: Raises an explicit error if a session with the same *image* and
            the same *name* already exists instead of returning the information
            of it.

            .. versionadded:: 19.09.0
        :param mounts: The list of vfolder names that belongs to the current API
            access key.
        :param mount_map: Mapping which contains custom path to mount vfolder.
            Key and value of this map should be vfolder name and custom path.
            Default mounts or relative paths are under /home/work.
            If you want different paths, names should be absolute paths.
            The target mount path of vFolders should not overlap with the linux system folders.
            vFolders which has a dot(.) prefix in its name are not affected.
        :param mount_options: Mapping which contains extra options for vfolder.
        :param envs: The environment variables which always bypasses the jail policy.
        :param resources: The resource specification. (TODO: details)
        :param cluster_size: The number of containers in this compute session.
            Must be at least 1.

            .. versionadded:: 19.09.0
            .. versionchanged:: 20.09.0
        :param cluster_mode: Set the clustering mode whether to use distributed
            nodes or a single node to spawn multiple containers for the new session.

            .. versionadded:: 20.09.0
        :param tag: An optional string to annotate extra information.
        :param owner: An optional access key that owns the created session. (Only
            available to administrators)

        :returns: The :class:`ComputeSession` instance.
        """
        if name is not None:
            assert 4 <= len(name) <= 64, "Client session token should be 4 to 64 characters long."
        else:
            faker = Faker()
            name = f"pysdk-{faker.user_name()}"
        if mounts is None:
            mounts = []
        if mount_map is None:
            mount_map = {}
        if mount_options is None:
            mount_options = {}
        if resources is None:
            resources = {}
        if resource_opts is None:
            resource_opts = {}
        if domain_name is None:
            # Even if config.domain is None, it can be guessed in the manager by user information.
            domain_name = api_session.get().config.domain
        if group_name is None:
            group_name = api_session.get().config.group

        mounts.extend(api_session.get().config.vfolder_mounts)
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request("POST", f"/{prefix}")
        params: Dict[str, Any] = {
            "tag": tag,
            get_naming(api_session.get().api_version, "name_arg"): name,
            "config": {
                "mounts": mounts,
                "environ": envs,
                "resources": resources,
                "resource_opts": resource_opts,
                "scalingGroup": scaling_group,
            },
        }
        if api_session.get().api_version >= (6, "20220315"):
            params["dependencies"] = dependencies
            params["callback_url"] = callback_url
            params["architecture"] = architecture
        if api_session.get().api_version >= (6, "20200815"):
            params["clusterSize"] = cluster_size
            params["clusterMode"] = cluster_mode
        else:
            params["config"]["clusterSize"] = cluster_size
        if api_session.get().api_version >= (5, "20191215"):
            params["starts_at"] = starts_at
            params["bootstrap_script"] = bootstrap_script
            if assign_agent is not None:
                params["config"].update({
                    "mount_map": mount_map,
                    "mount_options": mount_options,
                    "preopen_ports": preopen_ports,
                    "agentList": assign_agent,
                })
            else:
                params["config"].update({
                    "mount_map": mount_map,
                    "mount_options": mount_options,
                    "preopen_ports": preopen_ports,
                })
        if api_session.get().api_version >= (4, "20190615"):
            params.update({
                "owner_access_key": owner_access_key,
                "domain": domain_name,
                "group": group_name,
                "type": type_,
                "enqueueOnly": enqueue_only,
                "maxWaitSeconds": max_wait,
                "reuseIfExists": not no_reuse,
                "startupCommand": startup_command,
            })
        if api_session.get().api_version > (4, "20181215"):
            params["image"] = image
        else:
            params["lang"] = image
        rqst.set_json(params)
        async with rqst.fetch() as resp:
            data = await resp.json()
            o = cls(name, owner_access_key)  # type: ignore
            if api_session.get().api_version[0] >= 5:
                o.id = UUID(data["sessionId"])
            o.created = data.get("created", True)  # True is for legacy
            o.status = data.get("status", "RUNNING")
            o.service_ports = data.get("servicePorts", [])
            o.domain = domain_name
            o.group = group_name
            return o

    @api_function
    @classmethod
    async def create_from_template(
        cls,
        template_id: str,
        *,
        name: str | Undefined = undefined,
        type_: str | Undefined = undefined,
        starts_at: str | None = None,  # not included in templates
        enqueue_only: bool | Undefined = undefined,
        max_wait: int | Undefined = undefined,
        dependencies: Sequence[str] | None = None,  # cannot be stored in templates
        callback_url: str | Undefined = undefined,
        no_reuse: bool | Undefined = undefined,
        image: str | Undefined = undefined,
        mounts: List[str] | Undefined = undefined,
        mount_map: Mapping[str, str] | Undefined = undefined,
        envs: Mapping[str, str] | Undefined = undefined,
        startup_command: str | Undefined = undefined,
        resources: Mapping[str, str | int] | Undefined = undefined,
        resource_opts: Mapping[str, str | int] | Undefined = undefined,
        cluster_size: int | Undefined = undefined,
        cluster_mode: ClusterMode | Undefined = undefined,
        domain_name: str | Undefined = undefined,
        group_name: str | Undefined = undefined,
        bootstrap_script: str | Undefined = undefined,
        tag: str | Undefined = undefined,
        scaling_group: str | Undefined = undefined,
        owner_access_key: str | Undefined = undefined,
    ) -> ComputeSession:
        """
        Get-or-creates a compute session from template.
        All other parameters provided  will be overwritten to template, including
        vfolder mounts (not appended!).
        If *name* is ``None``, it creates a new compute session as long as
        the server has enough resources and your API key has remaining quota.
        If *name* is a valid string and there is an existing compute session
        with the same token and the same *image*, then it returns the :class:`ComputeSession`
        instance representing the existing session.

        :param template_id: Task template to apply to compute session.
        :param image: The image name and tag for the compute session.
            Example: ``python:3.6-ubuntu``.
            Check out the full list of available images in your server using (TODO:
            new API).
        :param name: A client-side (user-defined) identifier to distinguish the session among currently
            running sessions.
            It may be used to seamlessly reuse the session already created.

            .. versionchanged:: 19.12.0

               Renamed from ``clientSessionToken``.
        :param type_: Either ``"interactive"`` (default) or ``"batch"``.

            .. versionadded:: 19.09.0
        :param enqueue_only: Just enqueue the session creation request and return immediately,
            without waiting for its startup. (default: ``false`` to preserve the legacy
            behavior)

            .. versionadded:: 19.09.0
        :param max_wait: The time to wait for session startup. If the cluster resource
            is being fully utilized, this waiting time can be arbitrarily long due to
            job queueing.  If the timeout reaches, the returned *status* field becomes
            ``"TIMEOUT"``.  Still in this case, the session may start in the future.

            .. versionadded:: 19.09.0
        :param no_reuse: Raises an explicit error if a session with the same *image* and
            the same *name* already exists instead of returning the information
            of it.

            .. versionadded:: 19.09.0
        :param mounts: The list of vfolder names that belongs to the current API
            access key.
        :param mount_map: Mapping which contains custom path to mount vfolder.
            Key and value of this map should be vfolder name and custom path.
            Default mounts or relative paths are under /home/work.
            If you want different paths, names should be absolute paths.
            The target mount path of vFolders should not overlap with the linux system folders.
            vFolders which has a dot(.) prefix in its name are not affected.
        :param envs: The environment variables which always bypasses the jail policy.
        :param resources: The resource specification. (TODO: details)
        :param cluster_size: The number of containers in this compute session.
            Must be at least 1.

            .. versionadded:: 19.09.0
            .. versionchanged:: 20.09.0
        :param cluster_mode: Set the clustering mode whether to use distributed
            nodes or a single node to spawn multiple containers for the new session.

            .. versionadded:: 20.09.0
        :param tag: An optional string to annotate extra information.
        :param owner: An optional access key that owns the created session. (Only
            available to administrators)

        :returns: The :class:`ComputeSession` instance.
        """
        if name is not undefined:
            assert 4 <= len(name) <= 64, "Client session token should be 4 to 64 characters long."
        else:
            name = f"pysdk-{secrets.token_urlsafe(8)}"

        if domain_name is undefined:
            # Even if config.domain is None, it can be guessed in the manager by user information.
            domain_name = api_session.get().config.domain
        if group_name is undefined:
            group_name = api_session.get().config.group
        if mounts is undefined:
            mounts = []
        if api_session.get().config.vfolder_mounts:
            mounts.extend(api_session.get().config.vfolder_mounts)
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request("POST", f"/{prefix}/_/create-from-template")
        params: Dict[str, Any]
        params = {
            "template_id": template_id,
            "tag": tag,
            "image": image,
            "domain": domain_name,
            "group": group_name,
            get_naming(api_session.get().api_version, "name_arg"): name,
            "bootstrap_script": bootstrap_script,
            "enqueueOnly": enqueue_only,
            "maxWaitSeconds": max_wait,
            "dependencies": dependencies,
            "callbackURL": callback_url,
            "reuseIfExists": not no_reuse,
            "startupCommand": startup_command,
            "owner_access_key": owner_access_key,
            "type": type_,
            "starts_at": starts_at,
            "config": {
                "mounts": mounts,
                "mount_map": mount_map,
                "environ": envs,
                "resources": resources,
                "resource_opts": resource_opts,
                "scalingGroup": scaling_group,
            },
        }
        if api_session.get().api_version >= (6, "20200815"):
            params["clusterSize"] = cluster_size
            params["clusterMode"] = cluster_mode
        else:
            params["config"]["clusterSize"] = cluster_size
        params = cast(Dict[str, Any], drop(params, undefined))
        rqst.set_json(params)
        async with rqst.fetch() as resp:
            data = await resp.json()
            o = cls(name, owner_access_key if owner_access_key is not undefined else None)
            if api_session.get().api_version[0] >= 5:
                o.id = UUID(data["sessionId"])
            o.created = data.get("created", True)  # True is for legacy
            o.status = data.get("status", "RUNNING")
            o.service_ports = data.get("servicePorts", [])
            o.domain = domain_name
            o.group = group_name
            return o

    def __init__(self, name: str, owner_access_key: str = None) -> None:
        self.id = None
        self.name = name
        self.owner_access_key = owner_access_key

    @classmethod
    def from_session_id(cls, session_id: UUID) -> ComputeSession:
        o = cls(None, None)  # type: ignore
        o.id = session_id
        return o

    def get_session_identity_params(self) -> Mapping[str, str]:
        if self.id:
            identity_params = {
                "sessionId": str(self.id),
            }
        else:
            assert self.name is not None
            identity_params = {
                "sessionName": self.name,
            }
            if self.owner_access_key:
                identity_params["owner_access_key"] = self.owner_access_key
        return identity_params

    @api_function
    async def destroy(self, *, forced: bool = False, recursive: bool = False):
        """
        Destroys the compute session.
        Since the server literally kills the container(s), all ongoing executions are
        forcibly interrupted.
        """
        params = {}
        if self.owner_access_key is not None:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        if forced:
            params["forced"] = "true"
        if recursive:
            params["recursive"] = "true"

        rqst = Request(
            "DELETE",
            f"/{prefix}/{self.name}",
            params=params,
        )
        async with rqst.fetch() as resp:
            if resp.status == 200:
                return await resp.json()

    @api_function
    async def restart(self):
        """
        Restarts the compute session.
        The server force-destroys the current running container(s), but keeps their
        temporary scratch directories intact.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "PATCH",
            f"/{prefix}/{self.name}",
            params=params,
        )
        async with rqst.fetch():
            pass

    @api_function
    async def rename(self, new_id):
        """
        Renames Session ID of running compute session.
        """
        params = {"name": new_id}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "POST",
            f"/{prefix}/{self.name}/rename",
            params=params,
        )
        async with rqst.fetch():
            pass

    @api_function
    async def commit(self):
        """
        Commit a running session to a tar file in the agent host.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "POST",
            f"/{prefix}/{self.name}/commit",
            params=params,
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def export_to_image(self, new_image_name: str):
        """
        Commits running session to new image and then uploads to designated container registry.
        Requires Backend.AI server set up for per-user image commit feature (24.03).
        """
        params = {"image_name": new_image_name}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "POST",
            f"/{prefix}/{self.name}/imagify",
            params=params,
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def interrupt(self):
        """
        Tries to interrupt the current ongoing code execution.
        This may fail without any explicit errors depending on the code being
        executed.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "POST",
            f"/{prefix}/{self.name}/interrupt",
            params=params,
        )
        async with rqst.fetch():
            pass

    @api_function
    async def complete(self, code: str, opts: dict = None) -> Iterable[str]:
        """
        Gets the auto-completion candidates from the given code string,
        as if a user has pressed the tab key just after the code in
        IDEs.

        Depending on the language of the compute session, this feature
        may not be supported.  Unsupported sessions returns an empty list.

        :param code: An (incomplete) code text.
        :param opts: Additional information about the current cursor position,
            such as row, col, line and the remainder text.

        :returns: An ordered list of strings.
        """
        opts = {} if opts is None else opts
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "POST",
            f"/{prefix}/{self.name}/complete",
            params=params,
        )
        rqst.set_json({
            "code": code,
            "options": {
                "row": int(opts.get("row", 0)),
                "col": int(opts.get("col", 0)),
                "line": opts.get("line", ""),
                "post": opts.get("post", ""),
            },
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_info(self):
        """
        Retrieves a brief information about the compute session.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "GET",
            f"/{prefix}/{self.name}",
            params=params,
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_logs(self, kernel_id: UUID | None = None):
        """
        Retrieves the console log of the compute session container.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        if kernel_id is not None:
            params["kernel_id"] = str(kernel_id)
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "GET",
            f"/{prefix}/{self.name}/logs",
            params=params,
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_dependency_graph(self):
        """
        Retrieves the root node of dependency graph of the compute session.
        """
        params = {}

        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key

        prefix = get_naming(api_session.get().api_version, "path")

        rqst = Request(
            "GET",
            f"/{prefix}/{self.name}/dependency-graph",
            params=params,
        )

        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_status_history(self):
        """
        Retrieves the status transition history of the compute session.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "GET",
            f"/{prefix}/{self.name}/status-history",
            params=params,
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def execute(
        self, run_id: str = None, code: str = None, mode: str = "query", opts: dict = None
    ):
        """
        Executes a code snippet directly in the compute session or sends a set of
        build/clean/execute commands to the compute session.

        For more details about using this API, please refer :doc:`the official API
        documentation <user-api/intro>`.

        :param run_id: A unique identifier for a particular run loop.  In the
            first call, it may be ``None`` so that the server auto-assigns one.
            Subsequent calls must use the returned ``runId`` value to request
            continuation or to send user inputs.
        :param code: A code snippet as string.  In the continuation requests, it
            must be an empty string.  When sending user inputs, this is where the
            user input string is stored.
        :param mode: A constant string which is one of ``"query"``, ``"batch"``,
            ``"continue"``, and ``"user-input"``.
        :param opts: A dict for specifying additional options. Mainly used in the
            batch mode to specify build/clean/execution commands.
            See :ref:`the API object reference <batch-execution-query-object>`
            for details.

        :returns: :ref:`An execution result object <execution-result-object>`
        """
        opts = opts if opts is not None else {}
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        if mode in {"query", "continue", "input"}:
            assert code is not None, "The code argument must be a valid string even when empty."
            rqst = Request(
                "POST",
                f"/{prefix}/{self.name}",
                params=params,
            )
            rqst.set_json({
                "mode": mode,
                "code": code,
                "runId": run_id,
            })
        elif mode == "batch":
            rqst = Request(
                "POST",
                f"/{prefix}/{self.name}",
                params=params,
            )
            rqst.set_json({
                "mode": mode,
                "code": code,
                "runId": run_id,
                "options": {
                    "clean": opts.get("clean", None),
                    "build": opts.get("build", None),
                    "buildLog": bool(opts.get("buildLog", False)),
                    "exec": opts.get("exec", None),
                },
            })
        elif mode == "complete":
            rqst = Request(
                "POST",
                f"/{prefix}/{self.name}",
                params=params,
            )
            rqst.set_json({
                "code": code,
                "options": {
                    "row": int(opts.get("row", 0)),
                    "col": int(opts.get("col", 0)),
                    "line": opts.get("line", ""),
                    "post": opts.get("post", ""),
                },
            })
        else:
            raise BackendClientError("Invalid execution mode: {0}".format(mode))
        async with rqst.fetch() as resp:
            return (await resp.json())["result"]

    @api_function
    async def upload(
        self,
        files: Sequence[str | Path],
        basedir: Optional[str | Path] = None,
        show_progress: bool = False,
    ):
        """
        Uploads the given list of files to the compute session.
        You may refer them in the batch-mode execution or from the code
        executed in the server afterwards.

        :param files: The list of file paths in the client-side.
            If the paths include directories, the location of them in the compute
            session is calculated from the relative path to *basedir* and all
            intermediate parent directories are automatically created if not exists.

            For example, if a file path is ``/home/user/test/data.txt`` (or
            ``test/data.txt``) where *basedir* is ``/home/user`` (or the current
            working directory is ``/home/user``), the uploaded file is located at
            ``/home/work/test/data.txt`` in the compute session container.
        :param basedir: The directory prefix where the files reside.
            The default value is the current working directory.
        :param show_progress: Displays a progress bar during uploads.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        base_path = Path.cwd() if basedir is None else Path(basedir).resolve()
        files = [Path(file).resolve() for file in files]
        total_size = 0
        for file_path in files:
            total_size += Path(file_path).stat().st_size
        tqdm_obj = tqdm(
            desc="Uploading files",
            unit="bytes",
            unit_scale=True,
            total=total_size,
            disable=not show_progress,
        )
        with tqdm_obj:
            attachments = []
            for file_path in files:
                try:
                    attachments.append(
                        AttachedFile(
                            str(Path(file_path).relative_to(base_path)),
                            ProgressReportingReader(str(file_path), tqdm_instance=tqdm_obj),
                            "application/octet-stream",
                        )
                    )
                except ValueError:
                    msg = 'File "{0}" is outside of the base directory "{1}".'.format(
                        file_path, base_path
                    )
                    raise ValueError(msg) from None

            rqst = Request(
                "POST",
                f"/{prefix}/{self.name}/upload",
                params=params,
            )
            rqst.attach_files(attachments)
            async with rqst.fetch() as resp:
                return resp

    @api_function
    async def download(
        self,
        files: Sequence[str | Path],
        dest: str | Path = ".",
        show_progress: bool = False,
    ):
        """
        Downloads the given list of files from the compute session.

        :param files: The list of file paths in the compute session.
            If they are relative paths, the path is calculated from
            ``/home/work`` in the compute session container.
        :param dest: The destination directory in the client-side.
        :param show_progress: Displays a progress bar during downloads.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "GET",
            f"/{prefix}/{self.name}/download",
            params=params,
        )
        rqst.set_json({
            "files": [*map(str, files)],
        })
        file_names = []
        async with rqst.fetch() as resp:
            loop = current_loop()
            tqdm_obj = tqdm(
                desc="Downloading files",
                unit="bytes",
                unit_scale=True,
                total=resp.content.total_bytes,
                disable=not show_progress,
            )
            reader = aiohttp.MultipartReader.from_response(resp.raw_response)
            with tqdm_obj as pbar:
                while True:
                    part = cast(aiohttp.BodyPartReader, await reader.next())
                    if part is None:
                        break
                    assert part.headers.get(hdrs.CONTENT_ENCODING, "identity").lower() == "identity"
                    assert part.headers.get(hdrs.CONTENT_TRANSFER_ENCODING, "binary").lower() in (
                        "binary",
                        "8bit",
                        "7bit",
                    )
                    fp = tempfile.NamedTemporaryFile(suffix=".tar", delete=False)
                    while True:
                        chunk = await part.read_chunk(DEFAULT_CHUNK_SIZE)
                        if not chunk:
                            break
                        await loop.run_in_executor(None, lambda: fp.write(chunk))
                        pbar.update(len(chunk))
                    fp.close()
                    with tarfile.open(fp.name) as tarf:
                        tarf.extractall(path=dest)
                        file_names.extend(tarf.getnames())
                    os.unlink(fp.name)
        return {"file_names": file_names}

    @api_function
    async def list_files(self, path: str | Path = "."):
        """
        Gets the list of files in the given path inside the compute session
        container.

        :param path: The directory path in the compute session.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "GET",
            f"/{prefix}/{self.name}/files",
            params=params,
        )
        rqst.set_json({
            "path": path,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def stream_app_info(self):
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        id_or_name = get_id_or_name(api_session.get().api_version, self)
        api_rqst = Request(
            "GET",
            f"/stream/{prefix}/{id_or_name}/apps",
            params=params,
        )
        async with api_rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def get_abusing_report(self):
        """
        Retrieves abusing reports of session's sibling kernels.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "GET",
            f"/{prefix}/{self.name}/abusing-report",
            params=params,
        )
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    async def start_service(
        self,
        app: str,
        *,
        port: int | Undefined = undefined,
        envs: dict[str, Any] | Undefined = undefined,
        arguments: dict[str, Any] | Undefined = undefined,
        login_session_token: str | Undefined = undefined,
    ) -> Mapping[str, Any]:
        """
        Starts application from Backend.AI session and returns access credentials
        to access AppProxy endpoint.
        """
        body: dict[str, Any] = {"app": app}
        if port is not undefined:
            body["port"] = port
        if envs is not undefined:
            body["envs"] = json.dumps(envs)
        if arguments is not undefined:
            body["arguments"] = json.dumps(arguments)
        if login_session_token is not undefined:
            body["login_session_token"] = login_session_token

        prefix = get_naming(api_session.get().api_version, "path")
        rqst = Request(
            "POST",
            f"/{prefix}/{self.name}/start-service",
        )
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            return await resp.json()

    # only supported in AsyncAPISession
    def listen_events(self, scope: Literal["*", "session", "kernel"] = "*") -> SSEContextManager:
        """
        Opens the stream of the kernel lifecycle events.
        Only the master kernel of each session is monitored.

        :returns: a :class:`StreamEvents` object.
        """
        if api_session.get().api_version[0] >= 6:
            request = Request(
                "GET",
                "/events/session",
                params={
                    **self.get_session_identity_params(),
                    "scope": scope,
                },
            )
        else:
            assert self.name is not None
            params = {
                get_naming(api_session.get().api_version, "event_name_arg"): self.name,
            }
            if self.owner_access_key:
                params["owner_access_key"] = self.owner_access_key
            path = get_naming(api_session.get().api_version, "session_events_path")
            request = Request(
                "GET",
                path,
                params=params,
            )
        return request.connect_events()

    stream_events = listen_events  # legacy alias

    # only supported in AsyncAPISession
    def stream_pty(self) -> WebSocketContextManager:
        """
        Opens a pseudo-terminal of the kernel (if supported) streamed via
        websockets.

        :returns: a :class:`StreamPty` object.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        id_or_name = get_id_or_name(api_session.get().api_version, self)
        request = Request(
            "GET",
            f"/stream/{prefix}/{id_or_name}/pty",
            params=params,
        )
        return request.connect_websocket(response_cls=StreamPty)

    # only supported in AsyncAPISession
    def stream_execute(
        self, code: str = "", *, mode: str = "query", opts: dict = None
    ) -> WebSocketContextManager:
        """
        Executes a code snippet in the streaming mode.
        Since the returned websocket represents a run loop, there is no need to
        specify *run_id* explicitly.
        """
        params = {}
        if self.owner_access_key:
            params["owner_access_key"] = self.owner_access_key
        prefix = get_naming(api_session.get().api_version, "path")
        id_or_name = get_id_or_name(api_session.get().api_version, self)
        opts = {} if opts is None else opts
        if mode == "query":
            opts = {}
        elif mode == "batch":
            opts = {
                "clean": opts.get("clean", None),
                "build": opts.get("build", None),
                "buildLog": bool(opts.get("buildLog", False)),
                "exec": opts.get("exec", None),
            }
        else:
            msg = "Invalid stream-execution mode: {0}".format(mode)
            raise BackendClientError(msg)
        request = Request(
            "GET",
            f"/stream/{prefix}/{id_or_name}/execute",
            params=params,
        )

        async def send_code(ws):
            await ws.send_json({
                "code": code,
                "mode": mode,
                "options": opts,
            })

        return request.connect_websocket(on_enter=send_code)


class InferenceSession(BaseFunction):
    """
    Provides various interactions with inference sessions in Backend.AI.
    """

    id: Optional[UUID]
    name: Optional[str]
    owner_access_key: Optional[str]
    created: bool
    status: str
    service_ports: List[str]
    domain: str
    group: str
    # endpoint: Endpoint

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str | None = None,
        access_key: str | None = None,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str = None,
        order: str = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of inference sessions.
        """
        return await fetch_paginated_result(
            "inference_session_list",
            {
                "status": (status, "String"),
                "access_key": (access_key, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def hello(cls) -> str:
        rqst = Request("GET", "/")
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_task_logs(
        cls,
        task_id: str,
        *,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        raise NotImplementedError

    @api_function
    @classmethod
    async def get_or_create(
        cls,
        image: str,
        *,
        name: Optional[str] = None,
        type_: str = SessionTypes.INFERENCE.value,
        starts_at: Optional[str] = None,
        enqueue_only: bool = False,
        max_wait: int = 0,
        no_reuse: bool = False,
        dependencies: Optional[Sequence[str]] = None,
        callback_url: Optional[str] = None,
        mounts: Optional[List[str]] = None,
        mount_map: Optional[Mapping[str, str]] = None,
        mount_options: Optional[Mapping[str, Mapping[str, str]]] = None,
        envs: Optional[Mapping[str, str]] = None,
        startup_command: Optional[str] = None,
        resources: Optional[Mapping[str, str]] = None,
        resource_opts: Optional[Mapping[str, str]] = None,
        cluster_size: int = 1,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        domain_name: Optional[str] = None,
        group_name: Optional[str] = None,
        bootstrap_script: Optional[str] = None,
        tag: Optional[str] = None,
        architecture: Optional[str] = None,
        scaling_group: Optional[str] = None,
        owner_access_key: Optional[str] = None,
        preopen_ports: Optional[List[int]] = None,
        assign_agent: Optional[List[str]] = None,
    ) -> InferenceSession:
        """
        Get-or-creates an inference session.
        """
        raise NotImplementedError

    @api_function
    @classmethod
    async def create_from_template(
        cls,
        template_id: str,
        *,
        name: str | Undefined = undefined,
        type_: str | Undefined = undefined,
        starts_at: Optional[str] = None,
        enqueue_only: bool | Undefined = undefined,
        max_wait: int | Undefined = undefined,
        dependencies: Optional[Sequence[str]] = None,  # cannot be stored in templates
        no_reuse: bool | Undefined = undefined,
        image: str | Undefined = undefined,
        mounts: List[str] | Undefined = undefined,
        mount_map: Mapping[str, str] | Undefined = undefined,
        envs: Mapping[str, str] | Undefined = undefined,
        startup_command: str | Undefined = undefined,
        resources: Mapping[str, int] | Undefined = undefined,
        resource_opts: Mapping[str, int] | Undefined = undefined,
        cluster_size: int | Undefined = undefined,
        cluster_mode: ClusterMode | Undefined = undefined,
        domain_name: str | Undefined = undefined,
        group_name: str | Undefined = undefined,
        bootstrap_script: str | Undefined = undefined,
        tag: str | Undefined = undefined,
        architecture: str | Undefined = undefined,
        scaling_group: str | Undefined = undefined,
        owner_access_key: str | Undefined = undefined,
    ) -> InferenceSession:
        """
        Get-or-creates an inference session from template.
        """
        raise NotImplementedError

    def __init__(self, name: str, owner_access_key: Optional[str] = None) -> None:
        self.id = None
        self.name = name
        self.owner_access_key = owner_access_key

    @classmethod
    def from_session_id(cls, session_id: UUID) -> InferenceSession:
        o = cls(None, None)  # type: ignore
        o.id = session_id
        return o

    def get_session_identity_params(self) -> Mapping[str, str]:
        if self.id:
            identity_params = {
                "sessionId": str(self.id),
            }
        else:
            assert self.name is not None
            identity_params = {
                "sessionName": self.name,
            }
            if self.owner_access_key:
                identity_params["owner_access_key"] = self.owner_access_key
        return identity_params

    @api_function
    async def destroy(self, *, forced: bool = False):
        """
        Destroys the inference session.
        """
        raise NotImplementedError

    @api_function
    async def restart(self):
        """
        Restarts the inference session.
        """
        raise NotImplementedError

    @api_function
    async def rename(self, new_id):
        """
        Renames Session ID or running inference session.
        """
        raise NotImplementedError

    @api_function
    async def commit(self):
        """
        Commit a running session to a tar file in the agent host.
        """
        raise NotImplementedError

    @api_function
    async def interrupt(self):
        """
        Tries to interrupt the current ongoing code execution.
        This may fail without any explicit errors depending on the code being
        executed.
        """
        raise NotImplementedError

    @api_function
    async def complete(self, code: str, opts: Optional[dict] = None) -> Iterable[str]:
        """
        Gets the auto-completion candidates from the given code string,
        as if an user has passed the tab key just after the code in
        IDEs.
        """
        raise NotImplementedError

    @api_function
    async def get_info(self):
        """
        Retrieves a brief information about the inference session.
        """
        raise NotImplementedError

    @api_function
    async def get_logs(self):
        """
        Retrieves the console log of the inference session container.
        """
        raise NotImplementedError

    @api_function
    async def get_status_history(self):
        """
        Retrieves the status transition history of the inference session.
        """
        raise NotImplementedError

    @api_function
    async def upload(
        self,
        files: Sequence[str | Path],
        basedir: Optional[str | Path] = None,
        show_progress: bool = False,
    ):
        """
        Uploads the given list of files to the inference session.
        """
        raise NotImplementedError

    @api_function
    async def download(
        self,
        files: Sequence[str | Path],
        dest: str | Path = ".",
        show_progress: bool = False,
    ):
        """
        Downloads the given list of files from the inference session.
        """
        raise NotImplementedError

    @api_function
    async def list_files(self, path: str | Path = "."):
        """
        Gets the list of files in the given path inside the inference session
        container.
        """
        raise NotImplementedError

    @api_function
    async def stream_app_info(self):
        raise NotImplementedError

    @api_function
    async def get_abusing_report(self):
        """
        Retrieves abusing reports of session's sibling kernels.
        """
        raise NotImplementedError


class StreamPty(WebSocketResponse):
    """
    A derivative class of :class:`~ai.backend.client.request.WebSocketResponse` which
    provides additional functions to control the terminal.
    """

    __slots__ = ("ws",)

    async def resize(self, rows, cols):
        await self.ws.send_str(
            json.dumps({
                "type": "resize",
                "rows": rows,
                "cols": cols,
            })
        )

    async def restart(self):
        await self.ws.send_str(
            json.dumps({
                "type": "restart",
            })
        )
