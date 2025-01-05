python_sources(
    name="src",
    sources=[
        "*.py",
        # FIXME: remove watcher.py from agent artifact after we settle down
        # binary-based agent watcher deployments
        # "!watcher.py",
    ],
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/agent/docker:src",  # not auto-inferred
        "src/ai/backend/agent/dummy:src",  # not auto-inferred
        "src/ai/backend/agent/kubernetes:src",  # not auto-inferred
        "src/ai/backend/runner:src",
        "src/ai/backend/helpers:src",
        "src/ai/backend/common/logging.py:src",  # not auto-inferred (due to lazy-loading plugins)
        "//:reqs#backend.ai-krunner-static-gnu",  # not auto-inferred
        ":resources",
        "!./__init__.py:src-watcher",
    ],
)
python_sources(
    name="src-watcher",
    sources=[
        "__init__.py",
        "watcher.py",
    ],
    dependencies=[
        ":resources",
        # Exclude transitive dependencies of the agent itself!
        "!./__init__.py:src",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/accelerator/**",
        "//src/ai/backend/testutils/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/web/**",
        "!//src/ai/backend/manager/**",
        "!//src/ai/backend/storage/**",
        "!//src/ai/backend/wsproxy/**",
        "!//src/ai/backend/client/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "src/ai/backend/kernel:src",  # included only in binary dists
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-agent",
        description="Backend.AI Agent",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "ag": "ai.backend.agent.cli:main",
            "ag.start-server": "ai.backend.agent.server:main",
        },
        "backendai_network_agent_v1": {
            "overlay": "ai.backend.agent.docker.intrinsic:OverlayNetworkPlugin",
            "host": "ai.backend.agent.docker.intrinsic:HostNetworkPlugin",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="pex",
    entry_point="ai.backend.cli.__main__",
    dependencies=[
        ":src",
        ":buildscript",
        "//src/ai/backend/kernel:src",  # included only in binary dists
        # Bundle cuda-open and mock accelerator plugins
        "//src/ai/backend/accelerator/cuda_open:lib",
        "//src/ai/backend/accelerator/cuda_open:buildscript",
        "//src/ai/backend/accelerator/mock:lib",
        "//src/ai/backend/accelerator/mock:buildscript",
        "!!stubs/trafaret:stubs",
        "!!./__init__.py:src-watcher",
    ],
)

pex_binary(
    name="backendai-agent",
    extra_build_args=["--scie", "lazy"],
    tags=["scie", "lazy"],
    entry_point="ai.backend.cli.__main__",
    output_path="${target_name_normalized}",
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-agent-fat",
    extra_build_args=["--scie", "eager"],
    tags=["scie", "fat"],
    entry_point="ai.backend.cli.__main__",
    output_path="${target_name_normalized}",
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-agent-watcher",
    extra_build_args=["--scie", "lazy"],
    tags=["scie", "lazy"],
    entry_point="watcher.py",
    output_path="${target_name_normalized}",
    dependencies=[
        ":src-watcher",
        "!!stubs/trafaret:stubs",
        "!!./__init__.py:src",
    ],
)

pex_binary(
    name="backendai-agent-watcher-fat",
    extra_build_args=["--scie", "eager"],
    tags=["scie", "fat"],
    entry_point="watcher.py",
    output_path="${target_name_normalized}",
    dependencies=[
        ":src-watcher",
        "!!stubs/trafaret:stubs",
        "!!./__init__.py:src",
    ],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-agent-*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
        " {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-agent",
        ":backendai-agent-watcher",
        ":backendai-agent-fat",
        ":backendai-agent-watcher-fat",
    ],
    tags=["checksum"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "py.typed",
    ],
)
