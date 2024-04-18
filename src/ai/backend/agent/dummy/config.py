from __future__ import annotations

from pydantic import AliasChoices, Field

from ai.backend.common import typed_validators as tv
from ai.backend.common.config import ConfigModel

default_core_idx = {0, 1, 2, 3, 4}


class LocalConfig(ConfigModel):
    agent: Agent = Field(default_factory=lambda: Agent)
    kernel: Kernel = Field(default_factory=lambda: Kernel)


class Agent(ConfigModel):
    intrinsic: Intrinsic = Field(default_factory=lambda: Intrinsic)
    delay: AgentDelay = Field(default_factory=lambda: AgentDelay)
    image: Image = Field(default_factory=lambda: Image)


class Intrinsic(ConfigModel):
    cpu_core_indexes: set = Field(
        default_factory=lambda: default_core_idx,
        validation_alias=AliasChoices("cpu_core_indexes", "cpu-core-indexes"),
    )
    memory_size: int = Field(
        default=34359738368,
        validation_alias=AliasChoices("memory_size", "memory-size"),
    )


class AgentDelay(ConfigModel):
    scan_image: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("scan_image", "scan-image"),
    )
    push_image: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("push_image", "push-image"),
    )
    pull_image: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("pull_image", "pull-image"),
    )
    destroy_kernel: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("destroy_kernel", "destroy-kernel"),
    )
    clean_kernel: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("clean_kernel", "clean-kernel"),
    )
    create_network: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("create_network", "create-network"),
    )
    destroy_network: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("destroy_network", "destroy-network"),
    )


class Image(ConfigModel):
    already_have: dict = Field(
        default_factory=dict,
        validation_alias=AliasChoices("already_have", "already-have"),
        description="Key: a string of image canonical, Value: hash. it can be a random string",
    )
    need_to_pull: list = Field(
        default_factory=list,
        validation_alias=AliasChoices("need_to_pull", "need-to-pull"),
        description="A string list of image canonical",
    )
    missing: list = Field(
        default_factory=list,
        description="A string list of image canonical",
    )


class Kernel(ConfigModel):
    use_fake_code_runner: bool = Field(
        default=True,
        validation_alias=AliasChoices("use_fake_code_runner", "use-fake-code-runner"),
        description="Create a DummyFakeCodeRunner when create a kernel. "
        "A DummyFakeCodeRunner does not communicate anything through sockets, "
        "while a DummyCodeRunner feeds and listens through its sockets.",
    )
    delay: KernelDelay = Field(default_factory=lambda: KernelDelay)
    creation_ctx_delay: KernelCreationCtxDelay = Field(
        default_factory=lambda: KernelCreationCtxDelay,
        validation_alias=AliasChoices("creation_ctx_delay", "creation-ctx-delay"),
    )


class KernelDelay(ConfigModel):
    check_status: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("check_status", "check-status"),
    )
    get_completions: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("get_completions", "get-completions"),
    )
    get_logs: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("get_logs", "get-logs"),
    )
    interrupt_kernel: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("interrupt_kernel", "interrupt-kernel"),
    )
    start_service: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("start_service", "start-service"),
    )
    start_model_service: tv.RandomFloat = Field(
        default=5.0,
        validation_alias=AliasChoices("start_model_service", "start-model-service"),
    )
    shutdown_service: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("shutdown_service", "shutdown-service"),
    )
    commit: tv.RandomFloat = Field(default=5.0)
    get_service_apps: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("get_service_apps", "get-service-apps"),
    )
    accept_file: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("accept_file", "accept-file"),
    )
    download_file: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("download_file", "download-file"),
    )
    download_single: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("download_single", "download-single"),
    )
    list_files: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("list_files", "list-files"),
    )


class KernelCreationCtxDelay(ConfigModel):
    prepare_scratch: tv.RandomFloat = Field(
        default=0.1,
        validation_alias=AliasChoices("prepare_scratch", "prepare-scratch"),
    )
    prepare_ssh: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("prepare_ssh", "prepare-ssh"),
    )
    spawn: tv.RandomFloat = Field(default=0.5)
    start_container: tv.RandomFloat = Field(
        default=2.0,
        validation_alias=AliasChoices("start_container", "start-container"),
    )
    mount_krunner: tv.RandomFloat = Field(
        default=1.0,
        validation_alias=AliasChoices("mount_krunner", "mount-krunner"),
    )
