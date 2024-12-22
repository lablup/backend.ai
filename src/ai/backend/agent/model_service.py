import asyncio
from pathlib import Path
from typing import Any, Mapping

import yaml
from trafaret import DataError

from ai.backend.agent.exception import AgentError
from ai.backend.common.config import model_definition_iv
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    RuntimeVariant,
    ServicePort,
    ServicePortProtocols,
    VFolderMount,
)


class ModelServiceManager:
    runtime_variant: RuntimeVariant
    model_folder: VFolderMount
    model_definition_path: str | None

    def __init__(
        self,
        runtime_variant: RuntimeVariant,
        model_folder: VFolderMount,
        *,
        model_definition_path: str | None = None,
    ) -> None:
        self.runtime_variant = runtime_variant
        self.model_folder = model_folder
        self.model_definition_path = model_definition_path

    async def load_model_definition(
        self,
        image_command: str | None = None,
    ) -> Any:
        """
        Generates a model definition config (check `model_definition_iv` for schema) based on
        the runtime configuration of the kernel. When `runtime_variant` is set as `CUSTOM` then
        model definition will be populated base on the YAML file located at `model_definition_path`
        (`model-definition.yaml` or `model-definition.yml` by default).
        """

        if self.runtime_variant != RuntimeVariant.CUSTOM and not image_command:
            raise AgentError(
                "image should have its own command when runtime variant is set to values other than CUSTOM!"
            )

        match self.runtime_variant:
            case RuntimeVariant.VLLM:
                _model = {
                    "name": "vllm-model",
                    "model_path": self.model_folder.kernel_path.as_posix(),
                    "service": {
                        "start_command": image_command,
                        "port": MODEL_SERVICE_RUNTIME_PROFILES[self.runtime_variant].port,
                        "health_check": {
                            "path": MODEL_SERVICE_RUNTIME_PROFILES[
                                self.runtime_variant
                            ].health_check_endpoint,
                        },
                    },
                }
                raw_definition = {"models": [_model]}

            case RuntimeVariant.HUGGINGFACE_TGI:
                _model = {
                    "name": "tgi-model",
                    "model_path": self.model_folder.kernel_path.as_posix(),
                    "service": {
                        "start_command": image_command,
                        "port": MODEL_SERVICE_RUNTIME_PROFILES[self.runtime_variant].port,
                        "health_check": {
                            "path": MODEL_SERVICE_RUNTIME_PROFILES[
                                self.runtime_variant
                            ].health_check_endpoint,
                        },
                    },
                }
                raw_definition = {"models": [_model]}

            case RuntimeVariant.NIM:
                _model = {
                    "name": "nim-model",
                    "model_path": self.model_folder.kernel_path.as_posix(),
                    "service": {
                        "start_command": image_command,
                        "port": MODEL_SERVICE_RUNTIME_PROFILES[self.runtime_variant].port,
                        "health_check": {
                            "path": MODEL_SERVICE_RUNTIME_PROFILES[
                                self.runtime_variant
                            ].health_check_endpoint,
                        },
                    },
                }
                raw_definition = {"models": [_model]}

            case RuntimeVariant.CMD:
                _model = {
                    "name": "image-model",
                    "model_path": self.model_folder.kernel_path.as_posix(),
                    "service": {
                        "start_command": image_command,
                        "port": 8000,
                    },
                }
                raw_definition = {"models": [_model]}

            case RuntimeVariant.CUSTOM:
                if self.model_definition_path:
                    model_definition_candidates = [self.model_definition_path]
                else:
                    model_definition_candidates = [
                        "model-definition.yaml",
                        "model-definition.yml",
                    ]

                _def_path: Path | None = None
                for filename in model_definition_candidates:
                    if (Path(self.model_folder.host_path) / filename).is_file():
                        _def_path = Path(self.model_folder.host_path) / filename
                        break

                if not _def_path:
                    raise AgentError(
                        f"Model definition file ({" or ".join([str(x) for x in model_definition_candidates])}) does not exist under vFolder"
                        f" {self.model_folder.name} (ID {self.model_folder.vfid})",
                    )
                try:
                    model_definition_yaml = await asyncio.get_running_loop().run_in_executor(
                        None, _def_path.read_text
                    )
                except FileNotFoundError as e:
                    raise AgentError(
                        "Model definition file (model-definition.yml) does not exist under"
                        f" vFolder {self.model_folder.name} (ID {self.model_folder.vfid})",
                    ) from e
                try:
                    raw_definition = yaml.load(model_definition_yaml, Loader=yaml.FullLoader)
                except yaml.error.YAMLError as e:
                    raise AgentError(f"Invalid YAML syntax: {e}") from e
        try:
            model_definition = model_definition_iv.check(raw_definition)
            assert model_definition is not None
        except DataError as e:
            raise AgentError(
                "Failed to validate model definition from vFolder"
                f" {self.model_folder.name} (ID {self.model_folder.vfid})",
            ) from e

    def create_environs(self, model_definition: Any) -> Mapping[str, Any]:
        environ: dict[str, Any] = {}
        for model in model_definition["models"]:
            if "BACKEND_MODEL_NAME" not in environ:
                environ["BACKEND_MODEL_NAME"] = model["name"]
            environ["BACKEND_MODEL_PATH"] = model["model_path"]
        return model_definition

    def create_service_port_definitions(
        self, model_definition: Any, existing_service_ports: list[ServicePort]
    ) -> list[ServicePort]:
        """
        Extracts service port definition of model services. Requires definition generated by
        `ModelServiceManager.create_service_port_definitions()`.
        """
        new_service_ports: list[ServicePort] = []
        for model in model_definition["models"]:
            if service := model.get("service"):
                if service["port"] in (2000, 2001):
                    raise AgentError("Port 2000 and 2001 are reserved for internal use")
                overlapping_services = [
                    s for s in existing_service_ports if service["port"] in s["container_ports"]
                ]
                if len(overlapping_services) > 0:
                    raise AgentError(
                        f"Port {service["port"]} overlaps with built-in service"
                        f" {overlapping_services[0]["name"]}"
                    )
                new_service_ports.append({
                    "name": f"{model["name"]}-{service["port"]}",
                    "protocol": ServicePortProtocols.PREOPEN,
                    "container_ports": (service["port"],),
                    "host_ports": (None,),
                    "is_inference": True,
                })

        return new_service_ports
