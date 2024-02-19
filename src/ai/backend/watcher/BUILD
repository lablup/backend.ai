python_sources(
    name="src",
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/watcher/agent/**",
        "//src/ai/backend/watcher/storage/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/watcher/agent/**",
        "//src/ai/backend/watcher/storage/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/cli/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-watcher",
        description="Backend.AI Watcher",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "watcher": "ai.backend.watcher.cli:main",
            "watcher.start-server": "ai.backend.watcher.server:main",
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
        # Bundle agent and storage watcher plugins
        "//src/ai/backend/watcher/agent:src",
        "//src/ai/backend/watcher/agent:buildscript",
        "//src/ai/backend/watcher/storage:src",
        "//src/ai/backend/watcher/storage:buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-watcher",
    fat=False,
    dependencies=[":pex"],
    tags=["scie", "lazy"],
)

scie_binary(
    name="backendai-watcher-fat",
    fat=True,
    dependencies=[":pex"],
    tags=["scie", "fat"],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-watcher-*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
        " {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-watcher",
        ":backendai-watcher-fat",
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
        "**/py.typed",
    ],
)
