python_sources(
    name="src",
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[],
    allowed_dependencies=[
        "//src/ai/backend/cli/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-storage-proxy",
        description="Backend.AI Storage Proxy",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "storage": "ai.backend.storage.cli:main",
            "storage.start-server": "ai.backend.storage.server:main",
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
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-storage-proxy",
    dependencies=[":pex"],
)

run_shell_command(
    name="checksum",
    command="find dist -name 'backendai-storage-*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum {} > {}.sha256'",
    workdir="/",
    execution_dependencies=[":backendai-storage"],
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
