"""
Parses and interpolates the service-definition templates stored as json in
``/etc/backend.ai/servce-defs`` of Backend.AI containers.

See more details at `the documentation about adding new kernel images
<https://docs.backend.ai/en/latest/dev/adding-kernels.html#service-ports>`_.
"""

import json
import logging
import shlex
from collections.abc import (
    Collection,
    Mapping,
    MutableMapping,
    Sequence,
)
from pathlib import Path
from typing import (
    Any,
    TypedDict,
)

import attrs

from . import service_actions
from .exception import DisallowedArgument, DisallowedEnvironment, InvalidServiceDefinition
from .interpolation.base import AbstractServiceInterpolator
from .interpolation.legacy import LegacyInterpolator
from .interpolation.registry import INTERPOLATORS
from .interpolation.types import InterpolationMode, InterpolationOption
from .logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger())


class Action(TypedDict):
    action: str
    args: Mapping[str, str | list[str] | bool]
    ref: str | None


@attrs.define(auto_attribs=True, slots=True)
class ServiceDefinition:
    command: str | list[str]
    shell: str | None = "bash"
    noop: bool = False
    url_template: str = ""
    prestart_actions: list[Action] = attrs.Factory(list)
    env: Mapping[str, str] = attrs.Factory(dict)
    allowed_envs: list[str] = attrs.Factory(list)
    allowed_arguments: list[str] = attrs.Factory(list)
    default_arguments: Mapping[str, None | str | list[str]] = attrs.Factory(dict)


class ServiceOptions(TypedDict, total=False):
    arguments: Mapping[str, str | list[str]]
    envs: Mapping[str, str]
    interpolation: InterpolationOption | None


class ServiceParser:
    variables: MutableMapping[str, str]
    services: dict[str, ServiceDefinition]

    def __init__(self, variables: MutableMapping[str, str]) -> None:
        self.variables = variables
        self.services = {}

    async def parse(self, path: Path) -> None:
        for service_def_file in path.glob("*.json"):
            log.debug("loading service-definition from {}", service_def_file)
            try:
                with service_def_file.absolute().open("rb") as fr:
                    raw_service_def = json.load(fr)
                    # translate naming differences
                    if "prestart" in raw_service_def:
                        raw_service_def["prestart_actions"] = raw_service_def["prestart"]
                        del raw_service_def["prestart"]
            except OSError as e:
                raise InvalidServiceDefinition(
                    f"could not read the service-def file: {service_def_file.name}"
                ) from e
            except json.JSONDecodeError as e:
                raise InvalidServiceDefinition(
                    f"malformed JSON in service-def file: {service_def_file.name}"
                ) from e
            name = service_def_file.stem
            try:
                self.services[name] = ServiceDefinition(**raw_service_def)
            except TypeError as e:
                raise InvalidServiceDefinition(e.args[0][11:]) from e  # lstrip "__init__() "

    def add_model_service(self, name: str, model_service_info: dict[str, Any]) -> None:
        service_def = ServiceDefinition(
            model_service_info["start_command"],
            shell=model_service_info["shell"],
            prestart_actions=model_service_info["pre_start_actions"] or [],
        )
        self.services[name] = service_def

    async def start_service(
        self,
        service_name: str,
        frozen_envs: Collection[str],
        opts: ServiceOptions,
    ) -> tuple[Sequence[str] | None, Mapping[str, str]]:
        if service_name not in self.services.keys():
            return None, {}
        service = self.services[service_name]
        if service.noop:
            return [], {}
        interpolator: AbstractServiceInterpolator
        option = opts.get("interpolation")
        if option is None:
            interpolator = LegacyInterpolator(self.variables)
        else:
            mode = InterpolationMode(option["mode"])
            interpolator = INTERPOLATORS[mode].from_option(self.variables, option)

        for action in service.prestart_actions:
            try:
                action_impl = getattr(service_actions, action["action"])
            except AttributeError as e:
                raise InvalidServiceDefinition(
                    f"Service-def for {service_name} used invalid action: {action['action']}"
                ) from e
            ret = await action_impl(interpolator, **action["args"])
            if (ref := action.get("ref")) is not None:
                self.variables[ref] = ret

        # Convert a script into cmdargs
        start_command = service.command
        if isinstance(start_command, str):
            shell = service.shell
            if shell:
                start_command = [shell, "-c", start_command]
            else:
                start_command = shlex.split(start_command)
        cmdargs = [*start_command]
        env = {}

        additional_arguments = dict(service.default_arguments)
        if "arguments" in opts.keys() and opts["arguments"]:
            for argname, argvalue in opts["arguments"].items():
                if argname not in service.allowed_arguments:
                    raise DisallowedArgument(
                        f"Argument {argname} not allowed for service {service_name}"
                    )
                additional_arguments[argname] = argvalue
        for arg_name, arg_value in additional_arguments.items():
            cmdargs.append(arg_name)
            if isinstance(arg_value, str):
                cmdargs.append(arg_value)
            elif isinstance(arg_value, list):
                cmdargs += arg_value
        cmdargs = interpolator.apply(cmdargs)

        if "envs" in opts.keys() and opts["envs"]:
            for env_name, env_value in opts["envs"].items():
                if env_name not in service.allowed_envs:
                    raise DisallowedEnvironment(
                        f"Environment variable {env_name} not allowed for service {service_name}"
                    )
                if env_name in frozen_envs:
                    raise DisallowedEnvironment(
                        f"Environment variable {env_name} can't be overwritten"
                    )
                env[env_name] = env_value
        for env_name, env_value in service.env.items():
            env_name, env_value = interpolator.apply([env_name, env_value])
            env[env_name] = env_value

        return cmdargs, env

    async def get_apps(self, selected_service: str = "") -> Sequence[Mapping[str, Any]]:
        def _format(service_name: str) -> Mapping[str, Any]:
            service_info: dict[str, Any] = {"name": service_name}
            service = self.services[service_name]
            if len(service.url_template) > 0:
                service_info["url_template"] = service.url_template
            if len(service.allowed_arguments) > 0:
                service_info["allowed_arguments"] = service.allowed_arguments
            if len(service.allowed_envs) > 0:
                service_info["allowed_envs"] = service.allowed_envs
            return service_info

        apps = []
        if selected_service:
            if selected_service in self.services.keys():
                apps.append(_format(selected_service))
        else:
            for service_name in self.services.keys():
                apps.append(_format(service_name))
        return apps
