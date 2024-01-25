from typing import Any

from aiohttp import web

from ai.backend.agent.docker.metadata.server import RootContext

# from ai.backend.agent.kernel import AbstractKernel
# from ai.backend.common.types import KernelId

root_context_app_key = web.AppKey("_root.context", RootContext)
docker_mode_app_key = web.AppKey("docker-mode", str)
config_app_key = web.AppKey("config", Any)  # type: ignore
# config_server_app_key = web.AppKey("config.server", Any)  # type: ignore
# kernel_registry_app_key = web.AppKey("kernel-registry", Mapping[KernelId, AbstractKernel])
