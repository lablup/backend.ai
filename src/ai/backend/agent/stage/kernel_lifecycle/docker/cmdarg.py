from dataclasses import dataclass
from typing import Optional, override

from ai.backend.agent.config.unified import ContainerSandboxType
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)


@dataclass
class CmdArgSpec:
    runtime_type: str
    runtime_path: Optional[str]
    sandbox_type: ContainerSandboxType
    jail_args: list[str]
    debug_kernel_runner: bool


class CmdArgSpecGenerator(ArgsSpecGenerator[CmdArgSpec]):
    pass


@dataclass
class CmdArgResult:
    cmdargs: list[str]


class CmdArgProvisioner(Provisioner[CmdArgSpec, CmdArgResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-cmdarg"

    @override
    async def setup(self, spec: CmdArgSpec) -> CmdArgResult:
        cmdargs: list[str] = []
        krunner_opts: list[str] = []
        if spec.sandbox_type == ContainerSandboxType.JAIL:
            cmdargs += [
                "/opt/kernel/jail",
                # "--policy",
                # "/etc/backend.ai/jail/policy.yml",
                # TODO: Update default Jail policy in images
            ]
            if spec.jail_args:
                cmdargs += map(lambda s: s.strip(), spec.jail_args)
            cmdargs += ["--"]
        if spec.debug_kernel_runner:
            krunner_opts.append("--debug")
        cmdargs += [
            "/opt/backend.ai/bin/python",
            "-s",
            "-m",
            "ai.backend.kernel",
            *krunner_opts,
            spec.runtime_type,
        ]
        if spec.runtime_path is not None:
            cmdargs.append(spec.runtime_path)
        return CmdArgResult(cmdargs=cmdargs)

    @override
    async def teardown(self, resource: CmdArgResult) -> None:
        pass


class CmdArgStage(ProvisionStage[CmdArgSpec, CmdArgResult]):
    """
    Stage for generating command-line arguments for the kernel runner.
    This stage prepares the command arguments based on the provided specifications.
    """
