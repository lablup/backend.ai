from dataclasses import dataclass
from typing import Any, cast, override

from aiodocker.docker import Docker
from pydantic import ValidationError

from ai.backend.agent.exception import InvalidModelConfigurationError
from ai.backend.common.asyncio import closing_async
from ai.backend.common.config import ModelDefinition
from ai.backend.common.stage.types import (
    Provisioner,
    SpecGenerator,
)
from ai.backend.common.types import (
    RuntimeVariant,
    ServicePort,
    ServicePortProtocols,
    SessionTypes,
    VFolderMount,
)


@dataclass
class ModelServiceSpecCheckArgs:
    image_canonical: str
    model_vfolder_mount: VFolderMount
    session_type: SessionTypes
    runtime_variant: RuntimeVariant
    model_definition: dict[str, Any] | None = None

    def to_model_service_spec(self, image_command: str | None) -> "ModelServiceSpec":
        return ModelServiceSpec(
            session_type=self.session_type,
            model_vfolder_mount=self.model_vfolder_mount,
            runtime_variant=self.runtime_variant,
            model_definition=self.model_definition,
            image_command=image_command,
        )


@dataclass
class ModelServiceSpec:
    session_type: SessionTypes
    model_vfolder_mount: VFolderMount
    runtime_variant: RuntimeVariant
    model_definition: dict[str, Any] | None
    image_command: str | None


class ModelServiceSpecCheckProvisioner(Provisioner[ModelServiceSpecCheckArgs, ModelServiceSpec]):
    @property
    @override
    def name(self) -> str:
        return "docker-model-service-check"

    @override
    async def setup(self, spec: ModelServiceSpecCheckArgs) -> ModelServiceSpec:
        image_command = await self._extract_image_command(spec.image_canonical)
        if spec.runtime_variant != "custom" and not image_command:
            raise InvalidModelConfigurationError(
                "image should have its own command when runtime variant is set to values other than CUSTOM!"
            )

        return spec.to_model_service_spec(image_command)

    async def _extract_image_command(self, image_canonical: str) -> str | None:
        async with closing_async(Docker()) as docker:
            result = await docker.images.get(image_canonical)
            return cast(str | None, result["Config"].get("Cmd"))

    @override
    async def teardown(self, resource: ModelServiceSpec) -> None:
        pass


class ModelServiceSpecGenerator(SpecGenerator[ModelServiceSpec]):
    def __init__(self, args: ModelServiceSpecCheckArgs) -> None:
        self._args = args
        self._provisioner = ModelServiceSpecCheckProvisioner()

    @override
    async def wait_for_spec(self) -> ModelServiceSpec:
        return await self._provisioner.setup(self._args)


@dataclass
class ModelServiceResult:
    model_definition: ModelDefinition
    service_ports: list[ServicePort]
    environ: dict[str, str]


class ModelServiceProvisioner(Provisioner[ModelServiceSpec, ModelServiceResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-model-service"

    @override
    async def setup(self, spec: ModelServiceSpec) -> ModelServiceResult:
        model_definition = self._get_model_definition(spec)
        if model_definition is None:
            raise InvalidModelConfigurationError(
                "Model definition is empty. Please check your model definition file"
            )

        environ: dict[str, str] = {}
        service_ports: list[ServicePort] = []
        for model in model_definition.models:
            environ["BACKEND_MODEL_NAME"] = model.name
            environ["BACKEND_MODEL_PATH"] = model.model_path
            if service := model.service:
                service_ports.append({
                    "name": f"{model.name}-{service.port}",
                    "protocol": ServicePortProtocols.PREOPEN,
                    "container_ports": (service.port,),
                    "host_ports": (None,),
                    "is_inference": True,
                })
        return ModelServiceResult(
            model_definition=model_definition,
            environ=environ,
            service_ports=service_ports,
        )

    def _get_model_definition(self, spec: ModelServiceSpec) -> ModelDefinition:
        if spec.model_definition is None:
            raise InvalidModelConfigurationError(
                "model_definition was not provided by Manager via internal_data."
                f" (runtime_variant={spec.runtime_variant})"
            )
        try:
            return ModelDefinition.model_validate(spec.model_definition)
        except ValidationError as e:
            raise InvalidModelConfigurationError(
                f"Invalid model definition from Manager: {e}"
            ) from e

    @override
    async def teardown(self, resource: ModelServiceResult) -> None:
        return
