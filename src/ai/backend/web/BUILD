python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
        "//:reqs#coloredlogs",  # indirectly referred by logging config string
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/testutils/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/account_manager/**",
        "!//src/ai/backend/manager/**",
        "!//src/ai/backend/agent/**",
        "!//src/ai/backend/storage/**",
        "!//src/ai/backend/wsproxy/**",
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
            "web": "ai.backend.web.cli.__main__:main",
            "web.start-server": "ai.backend.web.cli.start_server:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="backendai-webserver",
    **common_scie_config("lazy"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-webserver-fat",
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
        "find . -name 'backendai-webserver*' -not -name '*.sha256' | xargs -I {} sh -c"
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
