from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common import typed_validators as tv

default_core_idx = {0, 1, 2, 3, 4}


class LocalConfig(BaseModel):
    agent: Agent = Field(default_factory=lambda: Agent)
    kernel_creation_ctx: KernelCreationCtxDelay = Field(
        default_factory=lambda: KernelCreationCtxDelay
    )
    kernel: Kernel = Field(default_factory=lambda: Kernel)


class Agent(BaseModel):
    intrinsic: Intrinsic = Field(default_factory=lambda: Intrinsic)
    delay: AgentDelay = Field(default_factory=lambda: AgentDelay)
    image: Image = Field(default_factory=lambda: Image)
    kernel_creation_ctx_delay: KernelCreationCtxDelay = Field(
        default_factory=lambda: KernelCreationCtxDelay
    )


class Intrinsic(BaseModel):
    cpu_core_indexes: set = Field(default_factory=lambda: default_core_idx)
    memory_size: int = Field(default=34359738368)


class AgentDelay(BaseModel):
    scan_image: tv.RandomFloat = Field(default=0.1)
    push_image: tv.RandomFloat = Field(default=1.0)
    pull_image: tv.RandomFloat = Field(default=1.0)
    destroy_kernel: tv.RandomFloat = Field(default=1.0)
    clean_kernel: tv.RandomFloat = Field(default=1.0)
    create_network: tv.RandomFloat = Field(default=1.0)
    destroy_network: tv.RandomFloat = Field(default=1.0)


class Image(BaseModel):
    already_have: dict = Field(
        default_factory=dict,
        description="Key: a string of image canonical, Value: hash. it can be a random string",
    )
    need_to_pull: list = Field(
        default_factory=list,
        description="A string list of image canonical",
    )
    missing: list = Field(
        default_factory=list,
        description="A string list of image canonical",
    )


class KernelCreationCtxDelay(BaseModel):
    prepare_scratch: tv.RandomFloat = Field(default=0.1)
    prepare_ssh: tv.RandomFloat = Field(default=1.0)
    spawn: tv.RandomFloat = Field(default=0.5)
    start_container: tv.RandomFloat = Field(default=2.0)
    mount_krunner: tv.RandomFloat = Field(default=1.0)


class Kernel(BaseModel):
    use_fake_code_runner: bool = Field(
        default=True,
        description="Create a DummyFakeCodeRunner when create a kernel. "
        "A DummyFakeCodeRunner does not communicate anything through sockets, "
        "while a DummyCodeRunner feeds and listens through its sockets.",
    )
    delay: KernelDelay = Field()


class KernelDelay(BaseModel):
    check_status: tv.RandomFloat = Field(default=0.1)
    get_completions: tv.RandomFloat = Field(default=0.1)
    get_logs: tv.RandomFloat = Field(default=0.1)
    interrupt_kernel: tv.RandomFloat = Field(default=0.1)
    start_service: tv.RandomFloat = Field(default=1.0)
    start_model_service: tv.RandomFloat = Field(default=5.0)
    shutdown_service: tv.RandomFloat = Field(default=0.1)
    commit: tv.RandomFloat = Field(default=5.0)
    get_service_apps: tv.RandomFloat = Field(default=0.1)
    accept_file: tv.RandomFloat = Field(default=0.1)
    download_file: tv.RandomFloat = Field(default=0.1)
    download_single: tv.RandomFloat = Field(default=0.1)
    list_files: tv.RandomFloat = Field(default=0.1)
