import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import zmq
import zmq.asyncio
from tenacity import (
    AsyncRetrying,
    RetryError,
    TryAgain,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
)

from ai.backend.agent.data.kernel.kernel import KernelObject
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import (
    ContainerId,
    ServicePort,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ContainerCheckSpec:
    ownership_data: KernelOwnershipData
    container_id: ContainerId

    kernel_init_polling_attempt: int
    kernel_init_polling_timeout: float
    kernel_init_timeout: float

    kernel_object: KernelObject
    service_ports: Sequence[ServicePort]


class ContainerCheckSpecGenerator(ArgsSpecGenerator[ContainerCheckSpec]):
    pass


class ContainerCheckResult:
    pass


class ContainerCheckProvisioner(Provisioner[ContainerCheckSpec, ContainerCheckResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-container-check"

    @override
    async def setup(self, spec: ContainerCheckSpec) -> ContainerCheckResult:
        try:
            async for attempt in AsyncRetrying(
                wait=wait_fixed(0.3),
                stop=(
                    stop_after_attempt(spec.kernel_init_polling_attempt)
                    | stop_after_delay(spec.kernel_init_polling_timeout)
                ),
                retry=(
                    retry_if_exception_type(zmq.error.ZMQError) | retry_if_exception_type(TryAgain)
                ),
            ):
                with attempt:
                    # Wait until bootstrap script is executed.
                    # - Main kernel runner is executed after bootstrap script, and
                    #   check_status is accessible only after kernel runner is loaded.
                    async with asyncio.timeout(spec.kernel_init_timeout):
                        await spec.kernel_object.check_status()
                        # Update the service-ports metadata from the image labels
                        # with the extended template metadata from the agent and krunner.
                        live_services = await spec.kernel_object.get_service_apps()
                    if live_services["status"] != "failed":
                        for live_service in live_services["data"]:
                            for service_port in spec.service_ports:
                                if live_service["name"] == service_port["name"]:
                                    service_port.update(live_service)
                                    break
                    else:
                        log.warning(
                            "Failed to retrieve service app info, retrying (kernel:{}, container:{})",
                            spec.ownership_data.kernel_id,
                            spec.container_id,
                        )
                        raise TryAgain
            log.info(
                "create_kernel(kernel:{}, session:{}, container:{}) service apps initialized: {}",
                spec.ownership_data.kernel_id,
                spec.ownership_data.session_id,
                spec.container_id[:12],
                spec.service_ports,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Timeout during container startup (k:{str(spec.ownership_data.kernel_id)}, container:{spec.container_id})"
            )
        except asyncio.CancelledError:
            raise RuntimeError(
                f"Cancelled waiting of container startup (k:{str(spec.ownership_data.kernel_id)}, container:{spec.container_id})"
            )
        except RetryError:
            err_msg = (
                "Container startup failed, the container might be missing or failed to initialize "
                f"(k:{str(spec.ownership_data.kernel_id)}, container:{spec.container_id})"
            )
            log.exception(err_msg)
            raise RuntimeError(err_msg)
        except BaseException as e:
            log.exception(
                "unexpected error while waiting container startup (k: {}, e: {})",
                spec.ownership_data.kernel_id,
                repr(e),
            )
            raise
        return ContainerCheckResult()

    @override
    async def teardown(self, resource: ContainerCheckResult) -> None:
        pass


class ContainerCheckStage(ProvisionStage[ContainerCheckSpec, ContainerCheckResult]):
    pass
