python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/appproxy/worker/cli:src",  # not auto-inferred (due to lazy-loading cmdgroup)
        "src/ai/backend/appproxy/worker/api:src",  # not auto-inferred (due to lazy-loading aiohttp app builder)
        ":resources",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
    ],
    provides=python_artifact(
        name="backend.ai-appproxy-worker",
        description="Backend.AI AppProxy Worier",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "worker": "ai.backend.appproxy.worker.cli.__main__:main",
            "worker.start-server": "ai.backend.appproxy.worker.server:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
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

pex_binary(
    name="backendai-appproxy-worker",
    **common_scie_config("lazy"),
    dependencies=[
        ":src",
        ":buildscript",
    ],
)

pex_binary(
    name="backendai-appproxy-worker-fat",
    **common_scie_config("eager"),
    dependencies=[
        ":src",
        ":buildscript",
    ],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-appproxy-worker*' -not -name '*.sha256' | xargs -I {} sh -c"
        " 'sha256sum {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-appproxy-worker",
    ],
    tags=["checksum"],
)
