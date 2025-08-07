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

python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/appproxy/coordinator/cli:src",  # not auto-inferred (due to lazy-loading cmdgroup)
        "src/ai/backend/appproxy/coordinator/api:src",  # not auto-inferred (due to lazy-loading aiohttp app builder)
        "src/ai/backend/appproxy/coordinator/models/alembic:migrations",  # not auto-inferred
        ":resources",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-appproxy-coordinator",
        description="Backend.AI AppProxy Coordinator",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "app-proxy-coordinator": "ai.backend.appproxy.coordinator.cli.__main__:main",
            "app-proxy-coordinator.start-server": "ai.backend.appproxy.coordinator.server:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="backendai-appproxy-coordinator",
    **common_scie_config("lazy"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-appproxy-coordinator-fat",
    **common_scie_config("eager"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-appproxy-coordinator*' -not -name '*.sha256' | xargs -I {} sh -c"
        " 'sha256sum {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-appproxy-coordinator",
        ":backendai-appproxy-coordinator-fat",
    ],
    tags=["checksum"],
)
