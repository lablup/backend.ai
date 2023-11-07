python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/cli:src",
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/web/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/cli/**",
        "//src/ai/backend/common/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-client",
        description="Backend.AI Client SDK",
        license="MIT",
    ),
    entry_points={
        "backendai_cli_v10": {
            "_": "ai.backend.client.cli.main:main",
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
    name="backendai-client",
    dependencies=[":pex"],
)

run_shell_command(
    name="checksum",
    command="find dist -name 'backendai-client-*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum {} > {}.sha256'",
    workdir="/",
    execution_dependencies=[":backendai-client"],
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
