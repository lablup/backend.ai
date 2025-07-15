import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from aiodocker.docker import Docker
from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ai.backend.agent.exception import InvalidModelConfigurationError
from ai.backend.common.asyncio import closing_async
from ai.backend.common.config import ModelDefinition
from ai.backend.common.stage.types import (
    Provisioner,
    SpecGenerator,
)
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
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
    model_definition_path: Optional[str] = None

    def to_model_service_spec(self, image_command: Optional[str]) -> "ModelServiceSpec":
        return ModelServiceSpec(
            session_type=self.session_type,
            model_vfolder_mount=self.model_vfolder_mount,
            runtime_variant=self.runtime_variant,
            model_definition_path=self.model_definition_path,
            image_command=image_command,
        )


@dataclass
class ModelServiceSpec:
    session_type: SessionTypes
    model_vfolder_mount: VFolderMount
    runtime_variant: RuntimeVariant
    model_definition_path: Optional[str]
    image_command: Optional[str]


class ModelServiceSpecCheckProvisioner(Provisioner[ModelServiceSpecCheckArgs, ModelServiceSpec]):
    @property
    @override
    def name(self) -> str:
        return "docker-model-service-check"

    @override
    async def setup(self, spec: ModelServiceSpecCheckArgs) -> ModelServiceSpec:
        image_command = await self._extract_image_command(spec.image_canonical)
        if spec.runtime_variant != RuntimeVariant.CUSTOM and not image_command:
            raise InvalidModelConfigurationError(
                "image should have its own command when runtime variant is set to values other than CUSTOM!"
            )

        return spec.to_model_service_spec(image_command)

    async def _extract_image_command(self, image_canonical: str) -> Optional[str]:
        async with closing_async(Docker()) as docker:
            result = await docker.images.get(image_canonical)
            return result["Config"].get("Cmd")

    @override
    async def teardown(self, resource: ModelServiceSpec) -> None:
        # No teardown actions needed for this provisioner
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
        model_definition = await self._get_model_definition(spec)
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

    async def _get_model_definition(self, spec: ModelServiceSpec) -> ModelDefinition:
        image_command = spec.image_command
        model_folder = spec.model_vfolder_mount
        match spec.runtime_variant:
            case RuntimeVariant.VLLM:
                return await self._get_model_definition_from_vllm(model_folder, image_command)
            case RuntimeVariant.HUGGINGFACE_TGI:
                return await self._get_model_definition_from_tgi(model_folder, image_command)
            case RuntimeVariant.NIM:
                return await self._get_model_definition_from_nim(model_folder, image_command)
            case RuntimeVariant.CMD:
                return await self._get_model_definition_from_cmd(model_folder, image_command)
            case RuntimeVariant.CUSTOM:
                return await self._get_model_definition_from_custom(
                    model_folder, spec.model_definition_path
                )

    async def _get_model_definition_from_vllm(
        self, model_folder: VFolderMount, image_command: Optional[str]
    ) -> ModelDefinition:
        _model = {
            "name": "vllm-model",
            "model_path": model_folder.kernel_path.as_posix(),
            "service": {
                "start_command": image_command,
                "port": MODEL_SERVICE_RUNTIME_PROFILES[RuntimeVariant.VLLM].port,
                "health_check": {
                    "path": MODEL_SERVICE_RUNTIME_PROFILES[
                        RuntimeVariant.VLLM
                    ].health_check_endpoint,
                },
            },
        }
        try:
            return ModelDefinition(models=[_model])  # type: ignore[arg-type,list-item]
        except ValidationError as e:
            raise InvalidModelConfigurationError(f"Invalid model definition for VLLM: {e}") from e

    async def _get_model_definition_from_tgi(
        self, model_folder: VFolderMount, image_command: Optional[str]
    ) -> ModelDefinition:
        _model = {
            "name": "tgi-model",
            "model_path": model_folder.kernel_path.as_posix(),
            "service": {
                "start_command": image_command,
                "port": MODEL_SERVICE_RUNTIME_PROFILES[RuntimeVariant.HUGGINGFACE_TGI].port,
                "health_check": {
                    "path": MODEL_SERVICE_RUNTIME_PROFILES[
                        RuntimeVariant.HUGGINGFACE_TGI
                    ].health_check_endpoint,
                },
            },
        }
        try:
            return ModelDefinition(models=[_model])  # type: ignore[arg-type,list-item]
        except ValidationError as e:
            raise InvalidModelConfigurationError(f"Invalid model definition for TGI: {e}") from e

    async def _get_model_definition_from_nim(
        self, model_folder: VFolderMount, image_command: Optional[str]
    ) -> ModelDefinition:
        _model = {
            "name": "nim-model",
            "model_path": model_folder.kernel_path.as_posix(),
            "service": {
                "start_command": image_command,
                "port": MODEL_SERVICE_RUNTIME_PROFILES[RuntimeVariant.NIM].port,
                "health_check": {
                    "path": MODEL_SERVICE_RUNTIME_PROFILES[
                        RuntimeVariant.NIM
                    ].health_check_endpoint,
                },
            },
        }
        try:
            return ModelDefinition(models=[_model])  # type: ignore[arg-type,list-item]
        except ValidationError as e:
            raise InvalidModelConfigurationError(f"Invalid model definition for NIM: {e}") from e

    async def _get_model_definition_from_cmd(
        self, model_folder: VFolderMount, image_command: Optional[str]
    ) -> ModelDefinition:
        _model = {
            "name": "image-model",
            "model_path": model_folder.kernel_path.as_posix(),
            "service": {
                "start_command": image_command,
                "port": 8000,
            },
        }
        try:
            return ModelDefinition(models=[_model])  # type: ignore[arg-type,list-item]
        except ValidationError as e:
            raise InvalidModelConfigurationError(f"Invalid model definition for CMD: {e}") from e

    async def _get_model_definition_from_custom(
        self, model_folder: VFolderMount, model_definition_path: Optional[str]
    ) -> ModelDefinition:
        if model_definition_path:
            model_definition_candidates = [model_definition_path]
        else:
            model_definition_candidates = [
                "model-definition.yaml",
                "model-definition.yml",
            ]

        final_model_definition_path: Optional[Path] = None
        for filename in model_definition_candidates:
            if (Path(model_folder.host_path) / filename).is_file():
                final_model_definition_path = Path(model_folder.host_path) / filename
                break

        if not final_model_definition_path:
            raise InvalidModelConfigurationError(
                f"Model definition file ({' or '.join(model_definition_candidates)}) does not exist under VFolder"
                f" {model_folder.name} (ID {model_folder.vfid})",
            )
        try:
            model_definition_yaml = await asyncio.get_running_loop().run_in_executor(
                None, final_model_definition_path.read_text
            )
        except FileNotFoundError as e:
            raise InvalidModelConfigurationError(
                "Model definition file (model-definition.yml) does not exist under"
                f" vFolder {model_folder.name} (ID {model_folder.vfid})",
            ) from e
        try:
            yaml = YAML()
            raw_definition = yaml.load(model_definition_yaml)
        except YAMLError as e:
            raise InvalidModelConfigurationError(f"Invalid YAML syntax: {e}") from e
        try:
            return ModelDefinition(**raw_definition)
        except ValidationError as e:
            raise InvalidModelConfigurationError(f"Invalid model definition: {e}") from e

    @override
    async def teardown(self, resource: ModelServiceResult) -> None:
        return
