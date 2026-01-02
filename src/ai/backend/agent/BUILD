python_sources(
    name="src",
    sources=["**/*.py", "!watcher/**/*.py"],
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/runner:src",
        "src/ai/backend/helpers:src",
        "//:reqs#backend.ai-krunner-static-gnu",  # not auto-inferred
        ":resources",
    ],
)

python_sources(
    name="src-watcher",
    sources=["watcher/**/*.py"],
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/runner:src",
        "src/ai/backend/helpers:src",
        "//:reqs#backend.ai-krunner-static-gnu",  # not auto-inferred
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/accelerator/**",
        "//src/ai/backend/testutils/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/account_manager/**",
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
        ":src-watcher",
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
            "ag": "ai.backend.agent.cli.__main__:main",
            "ag.start-server": "ai.backend.agent.cli.start_server:main",
        },
        "backendai_network_agent_v1": {
            "overlay": "ai.backend.agent.docker.intrinsic:OverlayNetworkPlugin",
            "host": "ai.backend.agent.docker.intrinsic:HostNetworkPlugin",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

_common_pex_dependencies = [
    "//src/ai/backend/kernel:src",  # included only in binary dists
    # Bundle cuda-open and mock accelerator plugins
    "//src/ai/backend/accelerator/cuda_open:lib",
    "//src/ai/backend/accelerator/cuda_open:buildscript",
    "//src/ai/backend/accelerator/mock:lib",
    "//src/ai/backend/accelerator/mock:buildscript",
]

pex_binary(
    name="backendai-agent",
    **common_scie_config("lazy"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
        *_common_pex_dependencies,
    ],
)

pex_binary(
    name="backendai-agent-fat",
    **common_scie_config("eager"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
        *_common_pex_dependencies,
    ],
)

pex_binary(
    name="backendai-agent-watcher",
    **common_scie_config("lazy", entry_point="watcher/__main__.py"),
    dependencies=[
        ":src-watcher",
        ":buildscript",
        ":resources",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-agent-watcher-fat",
    **common_scie_config("eager", entry_point="watcher/__main__.py"),
    dependencies=[
        ":src-watcher",
        ":buildscript",
        ":resources",
        "!!stubs/trafaret:stubs",
    ],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-agent*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
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
        "docker/*.tar.gz",
        "docker/*.txt",
        "docker/*.bin",
    ],
)
