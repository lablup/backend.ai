python_sources(
    name="src",
    dependencies=[
        ":resources",
        "//:reqs#coloredlogs",  # indirectly referred by logging config string
    ],
)

visibility_private_component(
    allowed_dependents=[],
    allowed_dependencies=[
        "//src/ai/backend/cli/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/client/**",
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
        name="backend.ai-webserver",
        description="Backend.AI WebUI Host",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "web": "ai.backend.web.cli:main",
            "web.start-server": "ai.backend.web.server:main",
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
    name="backendai-webserver",
    fat=False,
    dependencies=[":pex"],
    tags=["scie", "lazy"],
)

scie_binary(
    name="backendai-webserver-fat",
    fat=True,
    dependencies=[":pex"],
    tags=["scie", "fat"],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-webserver-*' -not -name '*.sha256' | xargs -I {} sh -c"
        " 'sha256sum {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-webserver",
        ":backendai-webserver-fat",
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
        "static/**/*",
        "templates/**/*",
    ],
)
